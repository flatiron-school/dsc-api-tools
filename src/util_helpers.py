import yaml

def requirements_to_yaml(requirements_file, yaml_file):
    with open(requirements_file, 'r') as f:
        lines = f.readlines()
        
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            packages.append(line)

    yaml_data = {'dependencies': packages}

    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_data, f)