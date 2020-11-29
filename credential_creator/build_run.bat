@REM if you want to creat
@REM @set create_verifier="y"
@REM if you do not want to create it
@REM set create_verifier
@set create_verifier="y"
@set verifier_name=
@set verifier_country=
@set ca_key_name=verifier.key
@set ca_cert_name=verifier.crt

@set create_server="y"
@set server_name=127.0.0.1
@set server_country=DE
@set server_key_name=server.key
@set server_cert_name=server.csr
@set server_autosigned_cert_name=server.crt
@set server_serial=01

@set client_generic_name=tizio_caio
@set client_name=Caio Tizio
@set client_country=IT
@set client_key_name=%client_generic_name%.key
@set client_cert_name=%client_generic_name%.csr
@set client_signed_cert_name=%client_generic_name%.crt
@set client_serial=02

@set bundled_client_certificate_name=%client_generic_name%.p12
@set bundle_password=<pfx_password>

call docker-compose build
call docker-compose up
call docker-compose down