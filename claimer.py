import oci
import time
import sys
import os

oci_dir = os.path.expanduser("~/.oci")
os.makedirs(oci_dir, exist_ok=True)

config_path = os.path.join(oci_dir, "config")
key_path = os.path.join(oci_dir, "oci_api_key.pem")

with open(config_path, "w") as f:
    f.write(os.environ["OCI_CONFIG"])

with open(key_path, "w") as f:
    f.write(os.environ["OCI_KEY"])

with open(config_path, "r") as f:
    config_content = f.read()

lines = config_content.splitlines()
new_lines = []
for line in lines:
    if line.strip().startswith("key_file"):
        new_lines.append(f"key_file={key_path}")
    else:
        new_lines.append(line)

with open(config_path, "w") as f:
    f.write("\n".join(new_lines))

try:
    config = oci.config.from_file(config_path, "DEFAULT")
    compute_client = oci.core.ComputeClient(config, timeout=(15, 15))
    print("CONFIG_LOADED", flush=True)
except Exception as e:
    print(f"ERROR_CONFIG: {e}", flush=True)
    sys.exit(1)

COMPARTMENT_ID = os.environ["OCI_COMPARTMENT"]
SUBNET_ID = os.environ["OCI_SUBNET"]
IMAGE_ID = os.environ["OCI_IMAGE"]
SSH_PUBLIC_KEY = os.environ["OCI_SSH_KEY"]
AVAILABILITY_DOMAIN = "vtrY:AP-BATAM-1-AD-1"

instance_details = oci.core.models.LaunchInstanceDetails(
    display_name="Verlexy_Oracle_VPS",
    compartment_id=COMPARTMENT_ID,
    availability_domain=AVAILABILITY_DOMAIN,
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=2.0,       
        memory_in_gbs=12.0 
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        source_type="image",
        image_id=IMAGE_ID
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id=SUBNET_ID,
        assign_public_ip=True,
        display_name="verlexy_vnic"
    ),
    metadata={
        "ssh_authorized_keys": SSH_PUBLIC_KEY
    }
)

attempt = 1
max_attempts = 15

while attempt <= max_attempts:
    try:
        print(f"ATTEMPT #{attempt}", flush=True)
        response = compute_client.launch_instance(instance_details)
        print(f"SUCCESS: {response.data.id}", flush=True)
        sys.exit(0)
    except oci.exceptions.ServiceError as e:
        if e.status == 500 or "Out of capacity" in str(e.message) or "LimitExhausted" in str(e.code):
            print("OUT_OF_CAPACITY", flush=True)
        elif e.status == 429 or "Too many requests" in str(e.message):
            print("RATE_LIMITED_WAITING_120S", flush=True)
        else:
            print(f"API_ERROR: {e.message}", flush=True)
    except Exception as e:
        print(f"SYS_ERROR: {e}", flush=True)
        
    attempt += 1
    time.sleep(120)
