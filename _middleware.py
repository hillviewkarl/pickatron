from aioflask import AioFlask
from .app import app

def main(request, env):
    return AioFlask(app)(request, env)