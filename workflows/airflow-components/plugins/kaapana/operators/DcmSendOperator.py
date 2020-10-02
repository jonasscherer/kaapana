from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, default_project
from datetime import timedelta

class DcmSendOperator(KaapanaBaseOperator):

    def __init__(self,
                 dag,
                 ae_title='dataset',
                 pacs_host= 'ctp-service.flow.svc',
                 pacs_port='11112',
                 dicom_dir='',
                 env_vars=None,
                 execution_timeout=timedelta(minutes=5),
                 *args, **kwargs
                 ):

        if env_vars is None:
            env_vars = {}
        
        envs = {
            "HOST": str(pacs_host),
            "PORT": str(pacs_port),
            "AETITLE": str(ae_title),
            "DICOM_DIR": str(dicom_dir)
        }

        env_vars.update(envs)

        super().__init__(
            dag=dag,
            image="{}{}/dcmsend:1.0-vdev".format(default_registry, default_project),
            name="dcmsend",
            image_pull_secrets=["registry-secret"],
            env_vars=env_vars,
            execution_timeout=execution_timeout,
            *args, **kwargs
            )