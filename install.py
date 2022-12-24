import launch

if not launch.is_installed("jinja2"):
    launch.run_pip("install Jinja2==3.1.2", desc='Jinja2==3.1.2')
if not launch.is_installed("requests"):
    launch.run_pip("install requests==2.28.1", desc='requests==2.28.1')
if not launch.is_installed("spacy"):
    launch.run_pip("install spacy==3.0.8", desc='spacy==3.0.8')
    launch.run_pip("install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.4.1/en_core_web_sm-3.4.1.tar.gz", desc='Installing en_core_web_sm==3.4.1')
if not launch.is_installed("Send2Trash"):
    launch.run_pip("install Send2Trash==1.8.0", desc='Send2Trash==1.8.0')