from json import load, dump
import os

DEFAULT_CONFIG = {
  "db_host": "localhost",
  "db_port": 5432,
  "db_user": "postgres",
  "db_password": "atmos2025",
  "db_database": "postgres",
  "caminho_dados_previsao": "./plots",
  "use_ssh": False,
  "ssh_user": "",
  "ssh_ip": "",
  "ssh_password": ""
}

def get_config() -> dict:
    """
    Busca a configuração do script em $HOME/.config/inmet-scrap; caso não a encontre, irá criá-la neste caminho.
    """
    home_path = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    config_path = os.path.join(home_path, '.config','inmet-scrap')
    if not os.path.exists(config_path): os.makedirs(config_path)
    config_file_path = os.path.join(config_path, 'config_previsao.json')
    if not os.path.exists(config_file_path):
        config = create_config_file(config_path, home_path)
    else:
        with open(f'{config_path}/config_previsao.json', 'r') as f: config = load(f)
    return config

def create_config_file(config_path: str, home_path: str) -> dict:
    """
    Cria configuração no caminho definido nos parametros, definindo por padrão o caminho de saída como $HOME/inmet-data
    :param config_path: Caminho da configuração, sendo ele sempre $HOME/.config/inmet-scrap
    :param home_path: Pasta home do computador onde está rodando
    """
    with open(os.path.join(config_path, 'config_previsao.json'), 'w') as f:
        dump(DEFAULT_CONFIG, f)
    return dict(DEFAULT_CONFIG)

