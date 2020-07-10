import boto3
import time

client_cloud_formation_main = boto3.client('cloudformation', region_name='us-east-1')

def start():
    res = raw_input("Voce gostaria de destruir a stack: (Y/N) \n") 
    if res.lower()=='y': 
        print "Iniciando destruicao"
    else:
        print 'Cancelando'
        exit()

def verificar_delete_stack_main(stack_name):
    nao_finalizado = True
    while nao_finalizado:
        time.sleep(30)
        try:
            Stack = client_cloud_formation_main.describe_stacks(StackName=stack_name)['Stacks'][0]
            StackStatus = Stack['StackStatus']
            print StackStatus
            print 'Ainda nao finalizou'
        except Exception:
            nao_finalizado = False

def destroy_stack_web_site():
    print '######### Iniciando destruicao de Infra do site #########'
    stack_name = 'WebSiteInfraStack'
    response_main = client_cloud_formation_main.delete_stack(StackName=stack_name)
    print '######### Verificando se Infra do site foi destruida com sucesso #########'   
    verificar_delete_stack_main(stack_name=stack_name)
    print '######### Finalizada destruicao de infra do site com sucesso #########'  

def destroy_site():
    print '######### Buscando Informacoes de stack #########'
    response_main = client_cloud_formation_main.list_exports()
    bucket_name = None
    for export in response_main['Exports']:
        if export['Name'] == "WebSiteInfraStack:BucketName":
            bucket_name = export['Value']
    
    s3 = boto3.resource('s3', region_name='us-east-1')
    bucket = s3.Bucket(bucket_name)
    bucket.objects.all().delete()
    bucket.object_versions.delete()
    bucket.delete()

start()
destroy_site()
destroy_stack_web_site()



