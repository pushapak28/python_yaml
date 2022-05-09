#!/usr/bin/env python3
#
# COPYRIGHT Ericsson 2021
#
#
#
# The copyright to the computer program(s) herein is the property of
#
# Ericsson Inc. The programs may be used and/or copied only with written
#
# permission from Ericsson Inc. or in accordance with the terms and
#
# conditions stipulated in the agreement/contract under which the
#
# program(s) have been supplied.
#

# -*- coding: utf-8 -*-
"""
This python program helps to deploy and upgrade helm chart on a Kubernetes system pointed by
KUBECONFIG

usage: deployAndUpgrade.py [-h] -k KUBECONFIG -n NAMESPACE [-m RELEASE_NAME]
                           -a CHART_ARCHIVE [-d DEPENDENCY_CHART_ARCHIVE] -r
                           HELM_REPO [-b BASELINE_REVISION] [-z]
                           [-c DOCKER_CONFIG_JSON]

Test tool for HELM installation and upgrade

optional arguments:
  -h, --help            show this help message and exit
  -k KUBECONFIG, --kubernetes-admin-conf KUBECONFIG
                        Kubernetes admin conf to use
  -n NAMESPACE, --kubernetes-namespace NAMESPACE
                        Kubernetes namespace to use
  -m RELEASE_NAME, --helm-release-name RELEASE_NAME
                        Helm release name to be used for installation
  -a CHART_ARCHIVE, --chart-archive CHART_ARCHIVE
                        Helm chart archive to test
  -d DEPENDENCY_CHART_ARCHIVE, --dependency-chart-archive DEPENDENCY_CHART_ARCHIVE
                        Helm chart archive which contains the implicit
                        dependencies of the primary helm chart which is under
                        test
  -r HELM_REPO, --helm-repo HELM_REPO
                        Helm chart repository to get the baseline from
  -b BASELINE_REVISION, --baseline_chart_version BASELINE_REVISION
                        Revision of the baseline chart to upgrade from. This
                        is mandatory unless the --skip-upgrade-test switch is
                        used.
  -z, --skip-upgrade-test
                        Skip upgrade test. Needed if there is no baseline yet
                        to upgrade from.
  -c DOCKER_CONFIG_JSON, --armdocker-config-json DOCKER_CONFIG_JSON
                        Path to the config.json containing credentials for Docker


Note:
1. This python program has dependency on kubernetes python client
   (See https://pypi.org/project/kubernetes/).
   You can also use docker image bob-py3kubehelmbuilder, which comes with all dependencies
   pre-installed, to run this python.

2. This program is a slightly modified version of test.py contributed by ADP, which comes ready
   along with the above-mentioned docker image. It was required to modify the python script as it
   had hardcoded values for HELM Home directory as '/home/helmuser/' which usually does not match
   the users environment.

"""
import requests
import argparse
import datetime
import os
import subprocess
import time
from kubernetes import client, config


def valid_file_path(file_path):
    if os.path.isfile(file_path):
        return file_path
    else:
        raise argparse.ArgumentTypeError('The value "' + file_path +
                                         '" provided is not a readable file')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Test tool for HELM installation and upgrade')
    parser.add_argument('-k', '--kubernetes-admin-conf',
                        dest='kubernetes_admin_conf',
                        type=valid_file_path, required=True,
                        metavar="KUBECONFIG",
                        help="Kubernetes admin conf to use")

    parser.add_argument('-n', '--kubernetes-namespace',
                        dest='kubernetes_namespace', type=str, required=True,
                        metavar='NAMESPACE',
                        help='Kubernetes namespace to use')

    parser.add_argument('-m', '--helm-release-name',
                        dest='helm_release_name', type=str,
                        default='application-under-test',
                        required=False,
                        metavar='RELEASE_NAME',
                        help='Helm release name to be used for installation')

    parser.add_argument('-a', '--chart-archive',
                        dest='chart_archive', type=valid_file_path,
                        required=True,
                        metavar='CHART_ARCHIVE',
                        help='Helm chart archive to test')

    parser.add_argument('-d', '--dependency-chart-archive',
                        dest='dependency_chart_archive',
                        type=valid_file_path, required=False,
                        metavar='DEPENDENCY_CHART_ARCHIVE',
                        help='Helm chart archive which contains the '
                             'implicit dependencies of the primary helm chart '
                             'which is under test')

    parser.add_argument('-r', '--helm-repo',
                        dest='helm_repo',
                        type=str, required=True, metavar='HELM_REPO',
                        help='Helm chart repository to get the baseline from')

    parser.add_argument('-b', '--baseline_chart_version',
                        dest='baseline_chart_version',
                        type=str, required=False, metavar='BASELINE_REVISION',
                        help='Revision of the baseline chart to upgrade from. '
                             'This is mandatory unless the --skip-upgrade-test'
                             ' switch is used.')

    parser.add_argument('-z', '--skip-upgrade-test', action='store_true',
                        default=False, dest='skip_upgrade_test',
                        help='Skip upgrade test. '
                             'Needed if there is no baseline yet '
                             'to upgrade from.')

    parser.add_argument('-c', '--armdocker-config-json',
                            dest='config_json', type=str,
                            default='$HOME/.docker/config.json',
                            required=False,
                            metavar='DOCKER_CONFIG_JSON',
                            help='Path to the config.json containing credentials for Docker')

    args = parser.parse_args()

    if (not args.baseline_chart_version) and (not args.skip_upgrade_test):
        raise argparse.ArgumentTypeError(
                'Either --baseline_chart_version or '
                '--skip-upgrade-test needs to be specified')

    return args


def d(t0):
    return str(datetime.datetime.now() - t0)


def log(*message):
    now = datetime.datetime.now()
    print(now.date().isoformat() + ' ' + now.time().isoformat() +
          ': ' + str(*message))


# Earlier we used p.wait and it used to take ages.
# Now we have removed wait and yet we have checks to see
# if the command is executed successfully or not
def execute_command(command):
    # Execute a command and return stdout, crash in case of a non-zero rc
    log("<-------------------------------------------------->")
    log('Command: ' + command )

    proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                universal_newlines=True)
    std_out, std_err = proc.communicate()

    if proc.returncode != 0:
        log("Failed: " + std_err)
        raise ValueError('Command return unexpected error code: %d' %
                         -1)
    else:
        log("Success: " + std_out)

    log("<-------------------------------------------------->")
    return std_out


def helm_cleanup_namespace(namespace_name):
    # Delete all releases in a namespace
    log('Cleaning up namespace, deleting all releases in namespace')
    releases = execute_command('helm ls --all --namespace=' + namespace_name +
                               ' -q')
    if not releases:
        return
    for release_name in releases.strip().split('\n'):
        log('Cleaning up helm release: ' + release_name)
        helm_delete_release(release_name)


def helm_delete_release(release_name):
    # Uninstall release_name in current namespace with a 20000s timeout
    log('Deleting release: ' + release_name)
    delete_command = ('helm uninstall --debug --timeout=20000s ' +
                      release_name)
    execute_command(delete_command)


def helm_list_releases(namespace_name):
    # List all helm releases in the namespace
    list_command = 'helm ls --all --namespace=' + namespace_name
    execute_command(list_command)


def helm_release_exist_in_namespace(namespace_name):
    list_command = 'helm ls --all --namespace=' + namespace_name
    return bool(execute_command(list_command))


def helm_install_chart_archive(name, chart_archive, namespace_name):
    # Install chart_archive
    install_command = ('helm install --debug ' + name + ' ' +
                       chart_archive +
                       ' --namespace=' + namespace_name +
                       ' --wait --timeout 20000s')
    return execute_command(install_command)


def helm_install_chart_from_repo(helm_repo, chart_name, chart_version,
                                 release_name, target_namespace_name):
    log('Adding helm repo')
    repo_add_command = ('helm repo add --home=$HOME/.helm'
                        ' --debug ' + 'BASELINE' + ' ' + helm_repo)
    execute_command(repo_add_command)

    log('Updating the helm repo')
    repo_add_command = ('helm repo update')
    execute_command(repo_add_command)

    log('Installing chart')
    baseline_install_command = ('helm install --home=$HOME/.helm '
                                '  --debug --namespace=' +  target_namespace_name +
                                '     BASELINE/' + chart_name + ' '
                                '  --version=' + chart_version +
                                '  --wait --timeout 20000s' +
                                '  --name=' + release_name)
    execute_command(baseline_install_command)


def helm_wait_for_deployed_release_to_appear(expected_release_name,
                                             target_namespace_name):
    # Wait for helm release to appear on the list and exit with None,
    # or raise ValueError if timeout of counter*sleep seconds
    log('Waiting for helm release to reach deployed state')
    counter = 20
    while True:
        release_name = execute_command('helm ls --deployed ' + ' --namespace=' +
                                        target_namespace_name + ' -q').rstrip()
        if release_name == expected_release_name:
            return
        log('%s != %s' % (str(release_name), expected_release_name))
        if counter > 0:
            counter = counter - 1
            time.sleep(15)
        else:
            raise ValueError('Timeout waiting for release to reach '
                             ' deployed state')


def helm_upgrade_with_chart_archive(baseline_release_name, chart_archive,
                                    target_namespace_name):
    release_name = execute_command('helm ls --deployed ' + baseline_release_name +
                                   '  --namespace=' + target_namespace_name + ' -q').rstrip()

    if not release_name or release_name != baseline_release_name:
        raise ValueError('Unable to find expected baseline release: ' +
                         baseline_release_name)

    upgrade_command = ('helm upgrade %s %s --namespace %s --debug --wait '
                       '    --timeout 20000' % (baseline_release_name,
                                            chart_archive,
                                            target_namespace_name))
    execute_command(upgrade_command)

def create_secret(namespace, secret_name, config_file_path):
    # Create k8s secret 'armdocker' in namspace to hold docker config
    # and configure to pull images from armdocker
    create_secret_command = ('kubectl create secret generic ' + secret_name +
                             '  --from-file=.dockerconfigjson=' + config_file_path +
                             '  --type=kubernetes.io/dockerconfigjson '+
                             '  --namespace ' + namespace)

    execute_command(create_secret_command).rstrip()

    patch_service_account_command = ('kubectl patch serviceaccount default ' +
                                     '  -p \'{\"imagePullSecrets\": [{\"name\": \"armdocker\"}]}\'' +
                                     '  -n ' + namespace)

    execute_command(patch_service_account_command)


class KubernetesClient:
    def __init__(self, kubernetes_admin_conf):
        config.load_kube_config(config_file=kubernetes_admin_conf)
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1beta2Api()

    def find_namespace(self, namespace_name):
        # Find namespace and return name of namespace if it exists,
        # None otherwise
        v1_namespace_list = self.core_v1.list_namespace()
        # for i in v1_namespace_list.items:
        #     print(i.metadata.name)

        return next(filter(lambda x: x.metadata.name == namespace_name,
                           v1_namespace_list.items), None)

    def create_namespace(self, namespace_name):
        # Create namespace with name "namespace_name" and return namespace
        v1ns = client.V1Namespace()
        v1ns.metadata = {'name': namespace_name}
        self.core_v1.create_namespace(body=v1ns)
        namespace_item = self.find_namespace(namespace_name)
        if namespace_item is None:
            raise ValueError('Failed to create namespace: ' + namespace_name)
        return namespace_item

    def delete_namespace(self, namespace_name):
        # Delete k8s namespace
        self.core_v1.delete_namespace(name=namespace_name,
                                      body=client.V1DeleteOptions(),
                                      propagation_policy='foreground')

    def wait_for_namespace_to_be_deleted(self, namespace_name):
        # Wait for namespace to be deleted for count*sleep seconds,
        # else timeout with ValueError
        counter = 60
        while True:
            if not self.find_namespace(namespace_name):
                break
            if counter > 0:
                log('Waiting for namespace %s to be deleted.' % namespace_name)
                counter = counter - 1
                time.sleep(15)
            else:
                raise ValueError('Timeout waiting for namespace %s to be '
                                 'deleted.' % namespace_name)

    def wait_for_all_resources(self, namespace_name):
        # Wait for all resources to be up and running
        self.wait_for_all_pods_to_start(namespace_name)
        self.wait_for_all_api_resources(namespace_name, "replicaset")
        self.wait_for_all_api_resources(namespace_name, "deployment")

    def wait_for_all_pods_to_start(self, namespace_name):
        # Raise an error if all pods not running, else exit with a None
        def format_containers(i):
            if not i.status.container_statuses:
                return 'No container statuses'
            return '\n'.join(['\n        Containername: %s'
                              '\n                Ready: %s'
                              '\n              Waiting: %s' %
                              (c.name,
                               c.ready,
                               str(c.state.waiting).replace('\n', ''))
                              for c in i.status.container_statuses])

        log('Pods:')
        counter = 60
        while True:
            api_response = self.core_v1.list_namespaced_pod(namespace_name)
            log('\n'.join(['\nPodname: %s'
                           '\n    Phase: %s'
                           '\n    Containers: %s' %
                           (i.metadata.name, i.status.phase,
                            format_containers(i))
                           for i in api_response.items]))

            if all([i.status.phase == 'Running' and
                    all([cs.ready for cs in i.status.container_statuses])
                    for i in api_response.items]):
                break
            if counter > 0:
                counter = counter - 1
                time.sleep(15)
            else:
                raise ValueError('Timeout waiting for pods to reach '
                                 'Ready & Running')

    def wait_for_all_pods_to_terminate(self, namespace_name):
        # Print pod status, if no pods listed then break out
        # Raise error if pop termination times out
        log('Pods:')
        counter = 60
        while True:
            api_response = self.core_v1.list_namespaced_pod(namespace_name)
            if not api_response.items:
                break
            else:
                log('\n'.join(['\nPhase: %s  Podname: %s' %
                               (i.status.phase, i.metadata.name)
                               for i in api_response.items]))

            if counter > 0:
                counter = counter - 1
                time.sleep(15)
            else:
                raise ValueError('Timeout waiting for pods to terminate')

    def _get_name_actual_desired(self, output_line, api_resource):
        if api_resource == "deployment":
            name = output_line[0]
            actual = int(output_line[1].split("/")[0])
            expected = int(output_line[1].split("/")[1])
        elif api_resource == "replicaset":
            name = output_line[0]
            actual = int(output_line[2])
            expected = int(output_line[1])
        return name, actual, expected

    def wait_for_all_api_resources(self, namespace, api_resource,
                                   sleep=15, retries=20):
        # Wait for all pods in api_resoruce to be running
        attempt = 1
        count = 0
        while True:
            response = execute_command(
                "kubectl get " + api_resource + " --no-headers -n " + namespace
            ).splitlines()

            log('TRY(%s/%s)  %ss:' %
                (str(attempt).zfill(len(str(retries))),
                 str(retries),
                 api_resource)
            )
            total = len(response)
            for resource in response:
                resource = resource.split()
                name, actual, expected = self._get_name_actual_desired(
                    resource, api_resource
                )
                log("%s: Pods ready/desired: (%d/%d)" %
                    (name, actual, expected))

                if actual != expected:
                    attempt += 1
                    if attempt > retries:
                        raise TimeoutError("Retries exceeded")
                    time.sleep(sleep)
                    count = 0
                    break
                count += 1
            if count == total:
                return True

def main():
    args = parse_args()
    target_namespace_name = args.kubernetes_namespace
    chart_archive = args.chart_archive
    release_name = args.helm_release_name

    # Deduct a "chart_name" for using it as part of a release name.
    # Takes the chart archive and does a 'helm inspect chart' on it
    # takes the value part of the name (after the space) from the line
    # starting with 'name: '
    chart_name = list(filter(lambda x: x.startswith('name: '),
                             execute_command('helm inspect chart ' +
                                             chart_archive
                                             ).split('\n')))[0].split(' ')[1]

    helm_repo = args.helm_repo
    baseline_chart_version = args.baseline_chart_version

    kube = KubernetesClient(args.kubernetes_admin_conf)

    def cleanup_target_namespace():
        # Cleanup namespace by removing releases, pods and
        # deleting the namespace
        log('Ensure that target namespace has been cleaned up')
        namespace_item = kube.find_namespace(target_namespace_name)
        if namespace_item:
            if helm_release_exist_in_namespace(target_namespace_name):
                helm_cleanup_namespace(target_namespace_name)
                kube.wait_for_all_pods_to_terminate(target_namespace_name)
            kube.delete_namespace(target_namespace_name)
            kube.wait_for_namespace_to_be_deleted(target_namespace_name)

    def test_setup():
        cleanup_target_namespace()
        log('Setup 1: Ensure that target namespace exists')
        kube.create_namespace(target_namespace_name)

        create_secret(target_namespace_name, 'armdocker', args.config_json)

        if args.dependency_chart_archive:
            log('Setup 2: Install dependency chart archive')
            helm_install_chart_archive('dependency-release',
                                       args.dependency_chart_archive,
                                       target_namespace_name)
            log('Setup 3: Wait for all resources to be up')
            kube.wait_for_all_resources(target_namespace_name)

            log('Setup 4: List releases')
            helm_list_releases(target_namespace_name)

    def test_teardown():
        if args.dependency_chart_archive:
            log('Teardown: Delete dependency release')
            helm_delete_release('dependency-release')
        cleanup_target_namespace()

    def test_install():
        t = datetime.datetime.now()
        log('\n'
            'TC: Install test-app\n'
            'TCID: TC_MAINT_INSTALL_001\n')

        log('Test Step 1: Record test case start status and timestamp - %s'
            % d(t))

        log('Test Step 2: Install from chart archive - %s' % d(t))
        helm_install_chart_archive(release_name, chart_archive,
                                   target_namespace_name)

        log('Test Step 3: Wait for all resources to be up - %s' % d(t))
        kube.wait_for_all_resources(target_namespace_name)
        helm_wait_for_deployed_release_to_appear(release_name,
                                                 target_namespace_name)

        log('Test Step 4: Delete release - %s' % d(t))
        helm_delete_release(release_name)

    def test_upgrade():
        # TODO
        # This is broken with Helm 2 commands but this is part of
        # future implementation as there is nothing concrete to test right now
        t = datetime.datetime.now()
        log('\n'
            'TC: Upgrade test-app\n'
            'TCID: TC_MAINT_UPGRADE_001\n')

        log('Test Step 1: Record test case start status and timestamp - %s'
            % d(t))

        log('Test Step 2: Install baseline from helm repo - %s' % d(t))
        baseline_release_name = chart_name + '-baseline-release'
        print("Baseline name is: " + baseline_release_name)
        helm_install_chart_from_repo(helm_repo, chart_name,
                                     baseline_chart_version,
                                     baseline_release_name,
                                     target_namespace_name)

        log('Test Step 4: Wait for all resources to be up - %s' % d(t))
        kube.wait_for_all_resources(target_namespace_name)
        helm_wait_for_deployed_release_to_appear(baseline_release_name,
                                                 target_namespace_name)

        log('Test Step 5: Perform upgrade from baseline - %s')
        helm_upgrade_with_chart_archive(baseline_release_name, chart_archive,
                                        target_namespace_name)

        # upgrade_status = True  # Get it from somewhere

        # if not upgrade_status:
        #     log('Upgrade failed performing rollback')
        #     default_revision_number = '1'
        #     rollback_command = ("helm rollback " + chart_name +
        #                         " " + default_revision_number + " --wait ")
        #     execute_command(rollback_command)
        #     return

        # log('Upgrade successfully done for  : ' + chart_name)
        log('Test Step 6: Wait for all resources to be up - %s' % d(t))
        kube.wait_for_all_resources(target_namespace_name)
        helm_wait_for_deployed_release_to_appear(baseline_release_name,
                                                 target_namespace_name)

    test_setup()
    test_install()
    if not args.skip_upgrade_test:
        test_upgrade()
    test_teardown()


if __name__ == "__main__":
     main()
     