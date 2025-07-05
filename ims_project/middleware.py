from django.conf import settings
from django.http import HttpResponseRedirect
import re

class RemoveDuplicateScriptNameMiddleware:
    """
    Middleware to handle duplicate FORCE_SCRIPT_NAME prefixes in URLs.
    This happens when a browser includes the script name in the URL, but Django also adds it.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.script_name = getattr(settings, 'FORCE_SCRIPT_NAME', '').rstrip('/')
        if self.script_name:
            # Create regex pattern to match duplicate script name
            # e.g., /imstransform/imstransform/
            self.pattern = re.compile(f'^({self.script_name})({self.script_name})(.*)')
        else:
            self.pattern = None

    def __call__(self, request):
        if self.pattern and self.script_name:
            path = request.path_info
            match = self.pattern.match(path)
            if match:
                # Replace duplicate script name with single instance
                fixed_path = f"{self.script_name}{match.group(3)}"
                return HttpResponseRedirect(fixed_path)
        
        return self.get_response(request) 