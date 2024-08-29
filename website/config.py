import yaml

def load_config():
    """加载并返回配置文件内容"""
    with open('/app/website/static/config.yaml', 'r', encoding='utf-8') as file:
        return yaml.load(file, Loader=yaml.CLoader)