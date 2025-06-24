import yaml

def load_yaml_test(file_path):
    """
    Load a YAML file and return its content.
    
    Args:
        file_path (str): The path to the YAML file.
        
    Returns:
        dict: The content of the YAML file as a dictionary.
    """
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} does not exist.")
        return None
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")
        return None