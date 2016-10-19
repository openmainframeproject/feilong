
HYPERVISOR_TYPE = 'zvm'
ARCHITECTURE = 's390x'
ALLOWED_VM_TYPE = 'zLinux'
XCAT_MGT = 'zvm'

XCAT_RINV_HOST_KEYWORDS = {
    "zvm_host": "z/VM Host:",
    "zhcp": "zHCP:",
    "cec_vendor": "CEC Vendor:",
    "cec_model": "CEC Model:",
    "hypervisor_os": "Hypervisor OS:",
    "hypervisor_name": "Hypervisor Name:",
    "architecture": "Architecture:",
    "lpar_cpu_total": "LPAR CPU Total:",
    "lpar_cpu_used": "LPAR CPU Used:",
    "lpar_memory_total": "LPAR Memory Total:",
    "lpar_memory_used": "LPAR Memory Used:",
    "lpar_memory_offline": "LPAR Memory Offline:",
    "ipl_time": "IPL Time:",
    }

XCAT_DISKPOOL_KEYWORDS = {
    "disk_total": "Total:",
    "disk_used": "Used:",
    "disk_available": "Free:",
    }

XCAT_RESPONSE_KEYS = ('info', 'data', 'node', 'errorcode', 'error')
