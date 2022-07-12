// uniform vec2 iResolution;
// x, y position of the light
uniform vec2 lightPosition;
// Size of light in pixels
uniform float lightSize;
// direction
uniform vec2 lightDirectionV;
// field of view angle
uniform float lightAngle;

#define N 128

float terrain(vec2 samplePoint)
{
    // iChannel0(terrain) 
    float samplePointAlpha = texture(iChannel0, samplePoint).a;
    float sampleStepped = step(0.1, samplePointAlpha);
    float result = 1.0 - sampleStepped;
    // Soften the shadows. Comment out for hard shadows.
    // The closer the first number is to 1.0, the softer the shadows.
    result = mix(0.9, 1.0, result);
    return result;
}

// should be 'mainImage' for shadertoy
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Distance in pixels to the light
    float distanceToLight = length(lightPosition - fragCoord);
    vec2 samplep = fragCoord - lightPosition;
    vec2 seep = iMouse.xy - lightPosition;

    if (distanceToLight > lightSize)
    {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
    else if (acos(dot(samplep, lightDirectionV) / length(samplep)) > radians(lightAngle))
    {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
    else
    {

        // Normalize the fragment coordinate from (0.0, 0.0) to (1.0, 1.0)
        vec2 normalizedFragCoord = fragCoord/iResolution.xy;

        // normalize light coord
        vec2 normalizedLightCoord = lightPosition.xy/iResolution.xy;



        // Start our mixing variable at 1.0
        float lightAmount = 1.0;

        for(float i = 0.0; i < N; i++)
        {
            // A 0.0 - 1.0 ratio between where our current pixel is, and where the light is
            float t = i / N;
            // Grab a coordinate between where we are and the light
            vec2 samplePoint = mix(normalizedLightCoord, normalizedFragCoord, t);
            // Is there something there? If so, we'll assume we are in shadow
            float shadowAmount = terrain(samplePoint);
            // Multiply the light amount.
            // (Multiply in case we want to upgrade to soft shadows)
            lightAmount *= shadowAmount;
        }

        // Make shadow for terrain itself
        // float shadowAmount = terrain(normalizedFragCoord);
        // lightAmount *= shadowAmount;

        // float terrainUnmask = terrain(normalizedFragCoord);


        // Find out how much light we have based on the distance to our light
        lightAmount *= 1.0 - smoothstep(0.0, lightSize, distanceToLight);

        // We'll alternate our display between black and whatever is in channel 1
        vec4 blackColor = vec4(0.0, 0.0, 0.0, 1.0);

        // Our fragment color will be somewhere between black and channel 1
        // dependent on the value of b.
        vec4 ich1 = texture(iChannel1, normalizedFragCoord);
        float ich1_alpha = step(0.2, lightAmount);
        ich1 = ich1 * ich1_alpha;

        fragColor = mix(blackColor, ich1, lightAmount);


    }
    
}
