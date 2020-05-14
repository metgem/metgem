from invoke import Collection

import packaging.tasks

ns = Collection()
ns.add_collection(packaging.tasks, 'packaging')
ns.add_task(packaging.tasks.rc)
