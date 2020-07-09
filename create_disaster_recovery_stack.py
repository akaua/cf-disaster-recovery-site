import boto3
import json
import time
import os
import logger

client_cloud_formation_main = boto3.client('cloudformation', region_name='us-east-1')

def start():
    res = raw_input("Voce gostaria de criar a stack: (Y/N) \n") 
    if res.lower()=='y': 
        print "Iniciando Criacao"
    else:
        print 'Cancelando'
        exit()

def sync_to_s3(target_dir, aws_region, bucket_name):
    if not os.path.isdir(target_dir):
        raise ValueError('target_dir %r not found.' % target_dir)

    s3 = boto3.resource('s3', region_name=aws_region)
    try:
        s3.create_bucket(Bucket=bucket_name,
                         CreateBucketConfiguration={'LocationConstraint': aws_region})
    except ClientError:
        pass

    for filename in os.listdir(target_dir):
        logger.warn('Uploading %s to Amazon S3 bucket %s' % (filename, bucket_name))
        s3.Object(bucket_name, filename).put(Body=open(os.path.join(target_dir, filename), 'rb'))

        logger.info('File uploaded to https://s3.%s.amazonaws.com/%s/%s' % (
            aws_region, bucket_name, filename))

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


    sync_to_s3('./site', aws_region='us-east-1', bucket_name=bucket_name)

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
            'CallerReference': str(time()).replace(".", "")
            }
        )



start()
create_stack()
deploy_web_site()
