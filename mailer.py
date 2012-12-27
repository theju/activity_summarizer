import json
import importlib
import operator
from smtplib import SMTP
from email.mime.text import MIMEText

def main():
    settings = json.load(open("config/settings.json", "r"))
    services = json.load(open("config/services.json", "r"))
    stream = []
    for service in services:
        mod = importlib.import_module("services.%s" % service)
        service_class = getattr(mod, service.title())
        kwargs = services[service]
        kwargs.update({"settings": settings})
        inst = service_class(**services[service])
        stream.extend(inst.render())
    sorted(stream, key=operator.itemgetter(0))

    stream_as_text = "\n".join(map(lambda x: x[1], stream))
    msg = MIMEText(stream_as_text)
    msg["From"] = settings["email"]["from"]
    msg["To"] = ", ".join(settings["email"]["to"])
    msg["Subject"] = settings["email"]["subject"]

    host_config = {"host": settings["email"]["host"],
                   "port": settings["email"]["port"]}
    conn = SMTP(**host_config)
    auth_params = {"user": settings["email"]["username"], "password": settings["email"]["password"]}
    if settings["email"].get("use_tls") == True:
        conn.starttls()
    conn.login(**auth_params)
    # conn.set_debuglevel(True)
    conn.sendmail(settings["email"]["from"], settings["email"]["to"], msg.as_string())
    conn.quit()

if __name__ == "__main__":
    main()
