
import logging
import time

from celery.task import task

from energygraph.store.views import *


logger = logging.getLogger('energygraph')

@task()  #  @task(name="store.doTask")
def doTask( x , y ):
    logger.warning( "Running doTask in ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ" )


