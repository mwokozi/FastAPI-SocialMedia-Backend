#! /bin/bash 

SOURCE_DIRECTORY="/Users/mwokoziclarke/Python/uv_social_network"

if [[ $(pwd)  != "${SOURCE_DIRECTORY}" ]] ; then echo "has to be run in ${SOURCE_DIRECTORY}" && exit 1 ; fi


 


if [[ $# -le 0  ]]; then echo "Usage: ${SOURCE_DIRECTORY}" && exit 1 ; fi 


if [[ ! -d BACKUP ]]; then echo "creating backup directory" && mkdir BACKUP ; fi 


for file in $* 
do
if [[ !  -f $file ]] ; then echo  "${file} does not exists" && continue ; fi 
dest_filename=${file}.$( date +%Y%m%d-%H%M%S )
echo "backing up ${file}..."
cp ${file}  BACKUP/${dest_filename} && echo "Successfully backed up ${file}"

filenames+=(${dest_filename}) #append to array 
done 

echo "------------------------------------------------------------------------------------------"

for file in  ${filenames[@]} # loop over array values note: ${!filename[@]} would loop over the array indexes 
do
ls -al ${SOURCE_DIRECTORY}/BACKUP/${file} 
done
