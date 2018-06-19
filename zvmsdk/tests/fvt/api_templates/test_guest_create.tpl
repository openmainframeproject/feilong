{
  "guest":
  {
      "userid": "id001",
      "vcpus": 1,
      "memory": 1024,
      "user_profile": "",
      "disk_list":[
      {
          "size": "1g",
          "is_boot_disk": True,
          "disk_pool": "ECKD:eckdpool1"
      },
      {
          "size": "200000",
          "disk_pool": "FBA:fbapool1",
          "format": "ext3"
      }],
      "max_cpu": 10,
      "max_mem": "32G"
  }
}
