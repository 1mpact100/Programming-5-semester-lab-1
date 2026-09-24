import re
import requests
import sys
from importlib.abc import PathEntryFinder
from importlib.util import spec_from_loader


class URLLoader:
    def create_module(self, target):
        return None
    
    def exec_module(self, module):
        try:
            response = requests.get(module.__spec__.origin, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise ImportError(
                f"Cannot download remote module: {module.__spec__.origin}"
            ) from error
        source = response.content
        code = compile(source, module.__spec__.origin, mode="exec")
        exec(code, module.__dict__)
        

class URLFinder(PathEntryFinder):
    def __init__(self, url, modules, packages):
        self.url = url.rstrip("/")
        self.modules = modules
        self.packages = packages
        
    def find_spec(self, name, target=None):
        module_name = name.rsplit(".", 1)[-1]
        if module_name in self.packages:
            origin = "{}/{}/__init__.py".format(self.url, module_name)
            loader = URLLoader()
            spec = spec_from_loader(
                name,
                loader,
                origin=origin,
                is_package=True
            )
            spec.submodule_search_locations = [
                "{}/{}/".format(self.url, module_name)
            ]
            return spec
        elif module_name in self.modules:
            origin = "{}/{}.py".format(self.url, module_name)
            loader = URLLoader()
            return spec_from_loader(
                name,
                loader,
                origin=origin,
                is_package=False
            )
        
        else:
            return None

def url_hook(some_str):
      
    if not some_str.startswith(("http", "https")):
        raise ImportError
    try:
        response = requests.get(some_str, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Cannot access remote module host: {some_str}"
        ) from error
    data = response.text
    filenames = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*\.py", data)
    modnames = {name[:-3] for name in filenames}
    directory_names = re.findall(
        r"href=[\"']([a-zA-Z_][a-zA-Z0-9_]*)/[\"']",
        data
    )
    dirnames = set(directory_names)
    return URLFinder(some_str, modnames, dirnames)


sys.path_hooks.append(url_hook)
