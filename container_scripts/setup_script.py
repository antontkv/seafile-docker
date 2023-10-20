import json
import os
import re
import subprocess
import time

SERVER_PATH = "/seafile/server/seafile-server"
DATA_PATH = "/seafile/data"
SERVER_ROOT_PATH = "/seafile/server"
SEAFILE_LATEST = os.path.join(SERVER_ROOT_PATH, "seafile-server-latest")
SEAFILE_INSTALL_SCRIPT = os.path.join(SERVER_PATH, "setup-seafile.sh")
SEAFILE_SH = os.path.join(SERVER_PATH, "seafile.sh")
SEAHUB_SH = os.path.join(SERVER_PATH, "seahub.sh")
PWD_FILE = os.path.join(SERVER_ROOT_PATH, "conf/admin.txt")
GUNICORN_CONFIG = os.path.join(SERVER_ROOT_PATH, "conf/gunicorn.conf.py")
CCNET_CONFIG = os.path.join(SERVER_ROOT_PATH, "conf/ccnet.conf")
SEAHUB_CONFIG = os.path.join(SERVER_ROOT_PATH, "conf/seahub_settings.py")
WEBDAV_CONFIG = os.path.join(SERVER_ROOT_PATH, "conf/seafdav.conf")
AVATARS_DIR = os.path.join(SERVER_PATH, "seahub/media/avatars")
SF_VER = os.path.join(DATA_PATH, "seafile_version.txt")

WEBDAV_STR = """\
[WEBDAV]
port = 8080
share_name = /seafdav
"""
WEBDAV_ENABLE_STR = """\
enabled = true
"""
WEBDAV_DISABLE_STR = """\
enabled = false
"""


def wait_forever():
    while True:
        time.sleep(1)


def check_env(env: str, default: str):
    if os.getenv(env) is not None:
        return os.getenv(env)
    else:
        return default


def write_version_file():
    with open(SF_VER, "w") as f:
        f.write(os.getenv("SEAFILE_VERSION"))


def read_version_file() -> str:
    with open(SF_VER, "r") as f:
        return f.read()


def replace_in_file(filename: str, re_to_find: str, replace_with_this: str):
    with open(filename, "r") as f:
        file_content = f.read()
        new_file_content = re.sub(re_to_find, replace_with_this, file_content, flags=re.MULTILINE)
    with open(filename, "w") as f:
        f.write(new_file_content)


def is_https(server_url: str) -> bool:
    return server_url.startswith("https://")


def port_validation(port: str) -> int:
    try:
        port = int(port)
    except TypeError:
        raise ValueError(f"Port value {port} is not valid integer")
    if 1 > port > 65536:
        raise ValueError(f"Port {port} in not in range of valid ports 1-65536")
    return port


def do_major_update(current_ver: str, old_ver: str) -> None:
    if current_ver == old_ver:
        return None

    update_7_1__8_0 = os.path.join(SERVER_PATH, "upgrade/upgrade_7.1_8.0.sh")
    update_map = {
        ("8.0.2", "8.0.3", "8.0.4", "8.0.5", "8.0.6", "8.0.7", "8.0.8"): {
            ("7.1.3", "7.1.4", "7.1.5"): (update_7_1__8_0,),
        }
    }

    for new_versions, old_versions in update_map.items():
        if current_ver in new_versions:
            for versions, update_scripts in old_versions.items():
                if old_ver in versions:
                    for script in update_scripts:
                        replace_in_file(script, r"read dummy", "")
                        subprocess.run([script], check=True)
                        write_version_file()
                        return None


def main():
    # Setting up URL info
    # Url parsing: scheme://hostname_or_IP:seahub_port:seafile_port
    server_url = check_env("SEAFILE_URL", "127.0.0.1:8000:8082")
    server_hostname = server_url.replace("https://", "").replace("http://", "")
    seahub_port = None
    seafile_port = None
    if (":") in server_hostname:
        url_info = server_hostname.split(":")
        server_hostname = url_info[0]
        seahub_port = port_validation(url_info[1])
        if len(url_info) >= 3:
            seafile_port = port_validation(url_info[2])

    # Running install script, if there is no data and running for the first time.
    if not os.path.exists(SF_VER):
        subprocess.run(
            [SEAFILE_INSTALL_SCRIPT, "auto", "-n", "seafile", "-i", server_hostname, "-p", "8082"], check=True
        )

        replace_in_file(GUNICORN_CONFIG, r"127\.0\.0\.1", "0.0.0.0")  # noqa

        admin_txt = {
            "email": check_env("SEAFILE_ADMIN_EMAIL", "me@example.com"),
            "password": check_env("SEAFILE_ADMIN_PASSWORD", "asecret"),
        }
        with open(PWD_FILE, "w") as f:
            json.dump(admin_txt, f)

        write_version_file()

    # Creating links for data files.
    data_files = ["ccnet", "conf", "seafile-data", "seahub-data", "seahub.db"]
    for df in data_files:
        src = os.path.join(SERVER_ROOT_PATH, df)
        dst = os.path.join(DATA_PATH, df)
        if os.path.exists(src) and not os.path.exists(dst):
            subprocess.run(["mv", src, dst], check=True)
        if os.path.exists(dst):
            subprocess.run(["ln", "-sf", dst, src], check=True)

    # Configuring WebDAV
    with open(WEBDAV_CONFIG, "w") as f:
        f.write(WEBDAV_STR)
        if check_env("ENABLE_WEBDAV", "false").lower() == "true":
            f.write(WEBDAV_ENABLE_STR)
        else:
            f.write(WEBDAV_DISABLE_STR)

    # Configure seahub_settings.py
    with open(SEAHUB_CONFIG, "r") as f:
        seahub_config_content = f.read()
    write_to_seahub_config = "\n"
    if "TIME_ZONE" not in seahub_config_content:
        write_to_seahub_config += f"TIME_ZONE = '{check_env('TZ', 'Etc/UTC')}'\n"
    if "FILE_SERVER_ROOT" not in seahub_config_content:
        write_to_seahub_config += "FILE_SERVER_ROOT = ''\n"

    if write_to_seahub_config != "\n":
        with open(SEAHUB_CONFIG, "a+") as f:
            f.write(write_to_seahub_config)

    # Configuring URLs
    service_url = "http://"
    file_server_root = "http://"
    if is_https(server_url):
        service_url = "https://"
        file_server_root = "https://"

    service_url += server_hostname
    file_server_root += server_hostname

    if seahub_port is not None:
        service_url += f":{seahub_port}"

    if seafile_port is not None:
        file_server_root += f":{seafile_port}"
    else:
        file_server_root += "/seafhttp"

    replace_in_file(CCNET_CONFIG, r"^SERVICE_URL = .*$", f"SERVICE_URL = {service_url}")
    replace_in_file(SEAHUB_CONFIG, r"^FILE_SERVER_ROOT = .*$", f"FILE_SERVER_ROOT = '{file_server_root}'")

    do_major_update(os.getenv("SEAFILE_VERSION"), read_version_file())

    # Running update scripts if container was recreated and there are existing data.
    if not os.path.exists(SEAFILE_LATEST):
        subprocess.run(["ln", "-s", SEAFILE_LATEST, SERVER_PATH], check=True)
    if not os.path.islink(AVATARS_DIR):
        print("The container was recreated, running minor-upgrade.sh to fix the media symlinks")
        minor_upgrade_script = os.path.join(SERVER_PATH, "upgrade/minor-upgrade.sh")
        replace_in_file(minor_upgrade_script, r"read dummy", "")
        subprocess.run([minor_upgrade_script], check=True)
        write_version_file()

    # Starting Seafile and Seahub.
    try:
        subprocess.run([SEAFILE_SH, "start"], check=True)
        subprocess.run([SEAHUB_SH, "start"], check=True)
    finally:
        if os.path.exists(PWD_FILE):
            os.remove(PWD_FILE)


if __name__ == "__main__":
    main()
    wait_forever()
