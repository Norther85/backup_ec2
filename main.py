import boto3
from datetime import datetime

ec2_client = boto3.client('ec2')

regions = [region['RegionName']
           for region in ec2_client.describe_regions()['Regions']]


def create_snapshots():
    for region in regions:
        print(f'Instances in EC2 Region {region}')
        ec2 = boto3.resource('ec2', region_name=region)
        instances = ec2.instances.filter(
            Filters=[
                {'Name': 'tag:backup', 'Values': ['true']}
            ]
        )
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat()
        for i in instances.all():
            for v in i.volumes.all():
                desc = "Backup {0}, {1}, {2}".format(i.id, v.id, timestamp)
                snapshot = ec2.create_snapshot(VolumeId=v.id, Description=desc)
            print(desc)


def prune_snapshots():
    '''
    Leave only one last snapshot for all instances
    '''
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    ec2 = boto3.client('ec2')
    for region in regions:
        print("Region", region)
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_snapshots(OwnerIds=[account_id])

        snapshots = response["Snapshots"]
        snapshots.sort(key=lambda x: x["StartTime"])
        snapshots = snapshots[:-1]

        for snapshot in snapshots:
            id = snapshot['SnapshotId']
            try:
                print("Deleting snapshot: ", id)
                ec2.delete_snapshot(SnapshotId=id)
            except:
                print("Can not remove ", id)


def delete_all_snapshots():
    '''
    Delete all snapshots for all instances
    '''
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    ec2 = boto3.client('ec2')
    for region in regions:
        print("Region", region)
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_snapshots(OwnerIds=[account_id])

        snapshots = response["Snapshots"]
        snapshots.sort(key=lambda x: x["StartTime"])

        for snapshot in snapshots:
            id = snapshot['SnapshotId']
            try:
                print("Deleting snapshot: ", id)
                ec2.delete_snapshot(SnapshotId=id)
            except:
                print("Can't remove ", id)
