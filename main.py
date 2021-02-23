#!/usr/bin/python
import argparse
import json
from datetime import datetime, timedelta

from modules.generators import attacker_generator, vm_generator
from modules.model import command, service


def convert_to_objects(conf):
    services = set()
    for s in conf['network']['services']:
        tmp = service.Service(s['name'])
        for c in s['commands']:
            co = command.Command(c['name'])
            for p in c['parameters']:
                co.add_parameter(p)
            tmp.add_command(co)

        services.add(tmp)
    conf['network']['services'] = services

    attacks = set()
    for c in conf['attacker']['attacks']:
        co = command.Command(c['name'])
        for p in c['parameters']:
            co.add_parameter(p)
        attacks.add(co)
    conf['attacker']['attacks'] = attacks

    conf['experiment']['start_date'] = datetime.strptime(conf['experiment']['start_date'], '%Y-%m-%d %H:%M')
    conf['experiment']['end_date'] = datetime.strptime(conf['experiment']['end_date'], '%Y-%m-%d %H:%M')


def configure(config_file):
    """Read the configuration file or creates the default one if it does not exist.

    Arguments:
        config_file {string} -- The configuration file

    Returns:
        dict -- The dictionary containing the configuration
    """
    conf = {}
    try:
        with open(config_file, 'r') as f:
            conf = json.load(f)

    except OSError:
        conf['network'] = {
            'vms': [
                {'behavior': 'user', 'services': ['ftpd'], 'max_actions': 5000},
                {'behavior': 'server', 'services': ['sshd', 'ftpd', 'httpd'], 'max_actions': 0},
                {'behavior': 'admin', 'services': ['sshd'], 'max_actions': 2500}
            ],
            'number_of_changes': 1,
            'prefix': '192.168.10.',
            'services': [
                {
                    'name': 'sshd',
                    'commands': [
                        {'name': '22', 'parameters': ['tester@&ip']},
                        {'name': 'sftp', 'parameters': ['tester@&ip']}
                    ]
                },
                {
                    'name': 'ftpd',
                    'commands': [
                        {'name': 'ftp', 'parameters': ['&ip']}
                    ]
                },
                {
                    'name': 'httpd',
                    'commands': [
                        {'name': 'wget', 'parameters': [
                            'http://&ip', '-r http://&ip']},
                        {'name': 'curl', 'parameters': ['http://&ip']}
                    ]
                }
            ]
        }
        conf['experiment'] = {
            'start_date': (datetime.now() + timedelta(1)).strftime('%Y-%m-%d %H:%M'),
            'end_date': (datetime.now() + timedelta(8)).strftime('%Y-%m-%d %H:%M')
        }
        conf['attacker'] = {
            "max_actions": 500,
            "attacks": [
                {
                    "name": "nmap",
                    "parameters": [
                        "&ip", "-sC 192.168.10.0/24", "-A 192.168.10.0/24", "-sV -F 192.168.10.0/24"
                    ]
                }
            ]
        }

        with open(config_file, 'w') as f:
            json.dump(conf, f, indent='\t')

    convert_to_objects(conf)
    return conf


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Python framework for an easy creation of a network model for scientific pcap creation.')
    parser.add_argument('-c', '--conf', nargs='?', default='conf/config.json',
                        help='specify an alternative configuration file')
    parser.add_argument('-t', '--test', action='store_true',
                        help='allows to run the framework without writing the outputs')

    args = parser.parse_args()

    conf = configure(args.conf)

    vms = vm_generator.generate(conf, args.test)

    attacker = attacker_generator.generate(vms, conf, args.test)

    if args.test:
        ret = 'vms:'
        i = 0
        for v in vms:
            ret += '\n\tvm_' + str(i) + ':' + ''.join(['\n\t\t' + line for line in str(v).split('\n')])
            i += 1

        ret += '\nattacker:' + ''.join(['\n\t' + line for line in str(attacker).split('\n')])

        print(ret)
