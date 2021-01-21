import pandas as pd

from modules.generators import action_generator, crontab_generator, vm_generator
from modules.model import attacker


def find_ip_and_mac(vms, prefix):
    """Finds a random IP and mac address that is not used by the vms
    
    Arguments:
        vms {list} -- The list of vms to consider
        prefix {str} -- The prefix to use for the IP address
    
    Returns:
        str,str -- The IP and mac address generated
    """
    ips, macs = set(), set()
    for v in vms:
        ips.add(v.ip)
        macs.add(v.mac)

    ip = vm_generator.rand_ip(prefix)
    while ip in ips:
        ip = vm_generator.rand_ip(prefix)

    mac = vm_generator.rand_mac()
    while mac in macs:
        mac = vm_generator.rand_mac()

    return ip, mac


def prepare_attacker(conf, vms):
    """Generates the attacker with its actions, attacks, IP and mac address
    
    Arguments:
        vms {list} -- The list of vms to attack
    
    Returns:
        attacker -- The generated attacker
    """
    ip, mac = find_ip_and_mac(vms, conf['network']['prefix'])
    h = attacker.Attacker(ip, mac)

    for a in conf['attacker']['attacks']:
        h.add_attack(a)

    actions = action_generator.attacker(h, conf, vms)
    for a in actions:
        h.add_action(a)

    return h


def write_data(h):
    """Writes the attacker to a CSV file on disk
    
    Arguments:
        h {Attacker} -- The attacker to write to disk
    """
    csv = {}
    for key, value in h.to_csv().items():
        if key in csv:
            csv[key] += [value]
        else:
            csv[key] = [value]

    df = pd.DataFrame(data=csv)

    keys = list(csv.keys())
    with open('vms/attacker.csv', 'w') as f:
        df.to_csv(path_or_buf=f, sep=',', index=False, columns=keys)

    crontab_generator.attacker(h)


def generate(vms, conf, test):
    """Generates the attacker
    
    Arguments:
        vms {list} -- The list of vms
        conf {dict} -- The dictionary containing the configuration
        test {boolean} -- Define if we need to write to disk or not
    
    Returns:
        attacker -- The generated attacker
    """
    a = prepare_attacker(conf, vms)

    if not test:
        write_data(a)

    return a
