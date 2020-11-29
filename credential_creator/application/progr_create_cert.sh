#!/usr/bin/env bash

# lsb_release -a
# cat /etc/lsb-release
#cat /etc/issue

if [[ ! -z ${create_verifier} ]]; then
    printf "Creating verifier\n"

    openssl genrsa -out ${ca_key_name} 4096
    openssl req -new -x509 -days 365 \
                    -subj "/C=${verifier_country}/CN=${verifier_name}" \
                    -key ${ca_key_name} -out ${ca_cert_name}
                    # -addext "role = verifier" \
    # this is valid for all the steps above in one line
    # openssl req -x509 -newkey rsa:2048 -keyout key.pem -out req.pem
else
    printf "Loading verifier\n"
    cp "./sharedstorage/${ca_cert_name}" ${ca_cert_name}
    cp "./sharedstorage/${ca_key_name}" ${ca_key_name}
fi

if [[ ! -z ${create_server} ]]; then
    printf "Creating server certificate\n"
    openssl genrsa -out ${server_key_name} 1024
    openssl req -new \
                -subj "/C=${server_country}/CN=${server_name}" \
                -key ${server_key_name} -out ${server_cert_name}

    openssl x509 -req -days 365 -in ${server_cert_name} -CA ${ca_cert_name} -CAkey ${ca_key_name} -set_serial ${server_serial} -out ${server_autosigned_cert_name}
fi

openssl genrsa -out $client_key_name 1024
openssl req -new \
            -subj "/C=${client_country}/CN=${client_name}" \
            -key $client_key_name -out ${client_cert_name}

openssl x509 -req -days 365 -in ${client_cert_name} -CA ${ca_cert_name} -CAkey ${ca_key_name} -set_serial ${client_serial} -out ${client_signed_cert_name}

openssl pkcs12 -export -clcerts \
                -in ${client_signed_cert_name} -inkey $client_key_name \
                -passout pass:${bundle_password} \
                -out $bundled_client_certificate_name

extension_array=(".crt" ".p12" ".csr" ".key" ".pem")
for file in ./*; do
    for exten in "${extension_array[@]}"; do
        if [[ $file == *"${exten}"* ]]; then
            # echo $file
            mv "$file" ./sharedstorage
            break
        fi
    done
done
