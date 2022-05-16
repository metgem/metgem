from invoke import Collection

import metgem_packaging.tasks

ns = Collection()
ns.add_collection(metgem_packaging.tasks, 'packaging')
ns.add_task(metgem_packaging.tasks.rc)
ns.add_task(metgem_packaging.tasks.uic)
