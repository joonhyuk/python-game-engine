// x, y position of the light
uniform vec2 lightPosition;
// Size of light in pixels
uniform float lightSize;
// 가리키는 방향
uniform float lightDirection;
// 비추는 각도
uniform float lightAngle;

#define N 100

float terrain(vec2 samplePoint)
{
    // iChannel0(지형 채널)에 위치한 점일 경우 알파=1 
    float samplePointAlpha = texture(iChannel0, samplePoint).a;
    float sampleStepped = step(0.1, samplePointAlpha);
    float result = 1.0 - sampleStepped;
    // Soften the shadows. Comment out for hard shadows.
    // The closer the first number is to 1.0, the softer the shadows.
    result = mix(0.9, 1.0, result);
    return result;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Distance in pixels to the light
    float distanceToLight = length(lightPosition - fragCoord);

    if (distanceToLight > lightSize)
    {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
    else
    {

        // Normalize the fragment coordinate from (0.0, 0.0) to (1.0, 1.0)
        vec2 normalizedFragCoord = fragCoord/iResolution.xy;

        // 라이트 좌표 노멀라이즈
        vec2 normalizedLightCoord = lightPosition.xy/iResolution.xy;

        // Start our mixing variable at 1.0
        float lightAmount = 1.0;

        for(float i = 0.0; i < N; i++)
        {
            // A 0.0 - 1.0 ratio between where our current pixel is, and where the light is
            float t = i / N;
            // Grab a coordinate between where we are and the light
            vec2 samplePoint = mix(normalizedFragCoord, normalizedLightCoord, t);
            // Is there something there? If so, we'll assume we are in shadow
            float shadowAmount = terrain(samplePoint);
            // Multiply the light amount.
            // (Multiply in case we want to upgrade to soft shadows)
            lightAmount *= shadowAmount;
        }

        // terrain에서 구한 지형 블락위치를 가지고 그림자 만들어주기
        // float shadowAmount = terrain(normalizedFragCoord);
        // lightAmount *= shadowAmount;

        // Find out how much light we have based on the distance to our light
        lightAmount *= 1.0 - smoothstep(0.0, lightSize, distanceToLight);

        // We'll alternate our display between black and whatever is in channel 1
        vec4 blackColor = vec4(0.0, 0.0, 0.0, 1.0);

        // Our fragment color will be somewhere between black and channel 1
        // dependent on the value of b.
        fragColor = mix(blackColor, texture(iChannel1, normalizedFragCoord), lightAmount);


    }
    
}
