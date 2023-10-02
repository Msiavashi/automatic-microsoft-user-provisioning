navigator.credentials.create = async function (options) {{
    console.log('Create operation intercepted! Options received: ', options);
    
    // Convert user.id to Hexadecimal format
    options.publicKey.user.id = arrayBufferToHex(options.publicKey.user.id);
    
    // Encode the challenge in Base64URL format
    options.publicKey.challenge = base64EncodeURL(new Uint8Array(options.publicKey.challenge));
    
    try {{
        let response = await fetch(
            '{}', 
            {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'x-api-key': '{}',
                }},
                body: JSON.stringify({{
                    publicKey: options.publicKey,
                    userid: '{}',
                    origin: window.origin,
                }}),
            }}
        );
        
        response = await response.json();
        
        // Process the response received from the server
        response.rawId = new Uint8Array(hexToByteArray(response.rawId)).buffer;
        response.id = base64EncodeURL(hexToByteArray(response.id));
        response.response.attestationObject = new Uint8Array(hexToByteArray(response.response.attestationObject)).buffer;
        response.response.clientDataJSON = str2ab(JSON.stringify(response.response.clientDataJSON));
        
        response.getClientExtensionResults = function () {{
            return {{
                hmacCreateSecret: true,
            }};
        }};
        
        console.log('Processed Response: ', response);
        return response;
        
    }} catch (error) {{
        console.error('Error during fetch operation: ', error);
    }}
}};

function arrayBufferToHex(buffer) {{
    return [...new Uint8Array(buffer)]
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}}

function hexToByteArray(hex) {{
    let bytes = [];
    for (let i = 0; i < hex.length; i += 2)
        bytes.push(parseInt(hex.substr(i, 2), 16));
    return bytes;
}}

function base64EncodeURL(byteArray) {{
    return btoa(
        Array.from(new Uint8Array(byteArray))
            .map(val => String.fromCharCode(val))
            .join('')
    )
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}}

function str2ab(str) {{
    const buf = new ArrayBuffer(str.length);
    const bufView = new Uint8Array(buf);
    for (let i = 0, strLen = str.length; i < strLen; i++) {{
        bufView[i] = str.charCodeAt(i);
    }}
    return buf;
}}
