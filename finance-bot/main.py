from twilio.rest import Client

# Credenciais do Twilio
account_sid = 'AC5407a52273e5b0dac3b1f4fe09e4db76'
auth_token = '9e5efd73931f1b14bd69991d928b91f0'
client = Client(account_sid, auth_token)

# Enviar mensagem no WhatsApp
message = client.messages.create(
    from_='whatsapp:+14155238886',  # Número do Twilio para WhatsApp
    to='whatsapp:+554188580721',    # Seu número com WhatsApp ativado
    body='Seu bot está funcionando! 🚀'
)

print(f'Mensagem enviada! SID: {message.sid}')
