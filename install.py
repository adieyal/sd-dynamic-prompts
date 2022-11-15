import launch

if not launch.is_installed("jinja2"):
    launch.run_pip("install Jinja2==3.1.2", desc='Installing Jinja2==3.1.2')
if not launch.is_installed("requests"):
    launch.run_pip("install requests==2.28.1", desc='Installing requests==2.28.1')
