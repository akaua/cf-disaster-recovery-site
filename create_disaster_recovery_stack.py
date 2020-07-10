import boto3
import json
import time
import os
import mimetypes

client_cloud_formation_main = boto3.client('cloudformation', region_name='us-east-1')

def start():
    res = raw_input("Voce gostaria de criar a stack: (Y/N) \n") 
    if res.lower()=='y': 
        print "Iniciando Criacao"
    else:
        print 'Cancelando'
        exit()

def upload_files(path,bucket_name):
    session = boto3.Session(region_name='us-east-1')
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            file_mime = mimetypes.guess_type(file)[0] or 'binary/octet-stream'
            with open(full_path, 'rb') as data:
                bucket.put_object(Key=full_path[len(path)+1:], Body=data, ContentType=file_mime)

def verificar_criacao_stack_main(stack_name):
    nao_finalizado = True
    while nao_finalizado:
        time.sleep(30)
        Stack = client_cloud_formation_main.describe_stacks(StackName=stack_name)['Stacks'][0]
        StackStatus = Stack['StackStatus']
        print StackStatus
        if StackStatus == 'CREATE_COMPLETE':
            nao_finalizado = False
        else:
            print 'Ainda nao finalizou'

def create_stack():
    print '######### Iniciando criacao de Infra para sustentar Web site #########'
    stack_name = 'WebSiteInfraStack'
    with open('./templates/web_site_infra.yaml', 'r') as cf_main_vpc_file:
        cft_main_vpc_template = cf_main_vpc_file.read()
        with open('./parameters/web_site_infra.json', 'r') as param_main_vpc_file:
            cft_main_vpc_param = json.loads(param_main_vpc_file.read())
            response = client_cloud_formation_main.create_stack(
                        StackName=stack_name,
                        TemplateBody=cft_main_vpc_template,
                        Parameters=cft_main_vpc_param,
                        Capabilities=[
                            'CAPABILITY_IAM'
                        ],
                        OnFailure='ROLLBACK'
                    )
    print '######### Verificando se Infra para sustentar web site foi criada com sucesso #########'   
    verificar_criacao_stack_main(stack_name=stack_name)
    print '######### Finalizada criacao de Infra para sustentar web site com sucesso #########'  


def deploy_web_site():
    print '######### Buscando Informacoes de stack #########'
    response_main = client_cloud_formation_main.list_exports()
    bucket_name = None
    cloud_front_id = None
    for export in response_main['Exports']:
        if export['Name'] == "WebSiteInfraStack:BucketName":
            bucket_name = export['Value']
        elif export['Name'] == "WebSiteInfraStack:CloudfrontID":
            cloud_front_id = export['Value']

    upload_files('./site',bucket_name=bucket_name)

    cloud_front = boto3.client('cloudfront')
    response = cloud_front.create_invalidation(
        DistributionId=cloud_front_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': [
                    '/*'
                    ],
                },
            'CallerReference': str(int(time.time()))
            }
        )

start()
create_stack()
deploy_web_site()
