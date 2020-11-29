export create_verifier="y"
export verifier_name=
export verifier_country=
export ca_key_name=verifier.key
export ca_cert_name=verifier.crt

export create_server="y"
export server_name=127.0.0.1
export server_country=DE
export server_key_name=server.key
export server_cert_name=server.csr
export server_autosigned_cert_name=server.crt
export server_serial=01

export client_generic_name=tizio_caio
export client_name=Caio Tizio
export client_country=IT
export client_key_name=${client_generic_name}.key
export client_cert_name=${client_generic_name}.csr
export client_signed_cert_name=${client_generic_name}.crt
export client_serial=02

export bundled_client_certificate_name=${client_generic_name}.p12
export bundle_password=

export permanent_storage=/host/permanent_storage

docker-compose build
docker-compose up
docker-compose down