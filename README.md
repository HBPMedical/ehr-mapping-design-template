# ehr-mapping-design-template

[![AUEB](https://img.shields.io/badge/AUEB-RC-red.svg)](http://rc.aueb.gr/el/static/home) [![HBP-SP8](https://img.shields.io/badge/HBP-SP8-magenta.svg)](https://www.humanbrainproject.eu/en/follow-hbp/news/category/sp8-medical-informatics-platform/)

This is a EHR mapping design template containing the folders and scripts needed to configure and run the EHR DataFactory pipeline on a machine.

## Requirements

- docker (v18)
- docker-compose (v1.22 - v1.8)

Datafactory User must be in the user group “docker”, so the scripts will run without the “sudo” command.
To do that, follow the below instructions:
Add the docker group if it doesn't already exist:

```shell
 sudo groupadd docker
 ```

Add the connected user "$USER" to the docker group. Change the user name to match your preferred user if you do not want to use your current user:

```shell
sudo gpasswd -a $USER docker
```

Either do a newgrp docker or log out/in to activate the changes to groups.
You can use `$ docker run hello-world`  to check if you can run docker without sudo.

## Instructions

1. We create a docker container with the name `demo_postgres` with the 3 databases which are needed by EHR DataFactory pipeline. These databases are:

- mipmap
- i2b2_capture
- i2b2_harmonized

To create this postgres container run:

```shell
sh build_postgres.sh
```

**Caution!** If `demo_postgres` container is already exist the script will drop the 3 databases and will create new ones.

2. Place the hospital csv files into the *source* folder and then launch MIPMap. Store the mapping xml file to the design root directory.

## Configuration

1. Update the *preprocess_step* files (for **preprocess** and **capture** step)
    - EncounterMapping.properties
    - PatientMapping.properties
    - txt files for unpivoting process

2. For **capture step** Copy the mapping xml file from the Design folder to the *capture_step* folder and rename the mapping xml file by adding the extension “.tmpl”

Open the xml file template file with an editor and find replace:

- The TARGET database name - “i2b2_capture.” -> “{{ .Env.i2b2_db_name }}.” (Note there is a “.” at end of each string)

- the following xml section

```xml
    <type>Relational</type>
   <relational>
     <driver>org.postgresql.Driver</driver>
     <uri>jdbc:postgresql://localhost:45432/i2b2_capture</uri>
     <login>postgres</login>
     <password>1234</password>
   </relational>
```

with this one:

```xml
<type>Relational</type>
   <relational>
     <driver>org.postgresql.Driver</driver>
     <uri>jdbc:postgresql://{{ .Env.i2b2_db_host }}:{{ default .Env.i2b2_db_port "5432" }}/{{ .Env.i2b2_db_name }}</uri>
     <login>{{ default .Env.i2b2_db_user "postgres" }}</login>
     <password>{{ default .Env.i2b2_db_password "postgres" }}</password>
   </relational>
```
3. For **harmonization step** Copy the mapping xml file from the Design folder to the *harmonize_step* folder and rename the mapping xml file by adding the extension “.tmpl”

Open the xml file template file with an editor and find replace:

- For the SOURCE database find and replace - “i2b2_capture.” to “{{ .Env.i2b2_db_name }}.” (Note there is a “.” at end of each string)

- Also in the SOURCE section, replace the following xml part:

```xml
    <type>Relational</type>
   <relational>
     <driver>org.postgresql.Driver</driver>
     <uri>jdbc:postgresql://localhost:45432/i2b2_capture</uri>
     <login>postgres</login>
     <password>1234</password>
   </relational>
```

with this one:

```xml
<type>Relational</type>
   <relational>
     <driver>org.postgresql.Driver</driver>
     <uri>jdbc:postgresql://{{ .Env.i2b2_db_host }}:{{ default .Env.i2b2_db_port "5432" }}/{{ .Env.i2b2_db_name }}</uri>
     <login>{{ default .Env.i2b2_db_user "postgres" }}</login>
     <password>{{ default .Env.i2b2_db_password "postgres" }}</password>
   </relational>
```

- For the TARGET database find and replace - “i2b2_harmonized.” to “{{ .Env.i2b2_db_harmonized_name }}.” (Note there is a “.” at end of each string)

- Also in the TARGET section, replace the following xml part:

```xml
    <type>Relational</type>
   <relational>
     <driver>org.postgresql.Driver</driver>
     <uri>jdbc:postgresql://localhost:45432/i2b2_harmonized</uri>
     <login>postgres</login>
     <password>1234</password>
   </relational>
```

with this one:

```xml
<type>Relational</type>
   <relational>
     <driver>org.postgresql.Driver</driver>
     <uri>jdbc:postgresql://{{ .Env.i2b2_db_harmonized_host }}:{{ default .Env.i2b2_db_harmonized_port "5432" }}/{{ .Env.i2b2_db_harmonized_name }}</uri>
     <login>{{ default .Env.i2b2_db__harmonized_user "postgres" }}</login>
     <password>{{ default .Env.i2b2_db_harmonized_password "postgres" }}</password>
   </relational>

```

### Running EHR pipeline

#### Step_1 - preprocess step

In DataFactory folder run:

```shell
sh ingestdata.sh preprocess
```

Auxiliary files are created in the same folder where the hospital csv files are located.

#### Step_2 - capture step

Caution! Auxilary files must be created first by the preprocessing step.
In DataFactory folder run:

```shell
sh ingestdata.sh capture
```

#### Step_3 - harmonization step

In DataFactory folder run:

```shell
sh ingestdata.sh harmonize
```

#### Step_4 - local data flattening step

In DataFactory folder run:

```shell
sh ingestdata.sh export
```

*harmonized_clinical_data.csv* is created in the mipmap output folder 
