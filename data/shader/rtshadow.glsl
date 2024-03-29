// uniform vec2 iResolution;
// x, y position of the light
uniform vec2 lightPosition;
// Size of light in pixels
uniform float lightSize;
// direction
uniform vec2 lightDirectionV;
// field of view angle
uniform float lightAngle;

uniform bool activated;

#define N 128

float terrain(vec2 samplePoint)
{
    // iChannel0(terrain) 
    float samplePointAlpha = texture(iChannel0, samplePoint).a;
    float sampleStepped = step(0.1, samplePointAlpha);  // minimum alpha to count
    float result = 1.0 - sampleStepped;
    // Soften the shadows. Comment out for hard shadows.
    // The closer the first number is to 1.0, the softer the shadows.
    result = mix(0.75, 1.0, result);
    return result;
}

// should be 'mainImage' for shadertoy
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    if (activated)
    {

        // Distance in pixels to the light
        float distanceToLight = length(lightPosition - fragCoord);
        vec2 samplep = fragCoord - lightPosition;
        vec2 normalizedFragCoord = fragCoord/iResolution.xy;

        float angleFromHeading = acos(dot(samplep, lightDirectionV) / length(samplep));
        // float angleFromHeading = acos(dot(samplep, vec2(0,1)) / length(samplep)) - radians(lightDirectionV);

        // if (distanceToLight > lightSize)
        // {
        //     fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        // }
        // else 
        if (angleFromHeading > radians(lightAngle))
        {
            // should be blacked out even on lights
            fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        }
        else
        {

            // Normalize the fragment coordinate from (0.0, 0.0) to (1.0, 1.0)
            // vec2 normalizedFragCoord = fragCoord/iResolution.xy;

            // normalize light coord
            vec2 normalizedLightCoord = lightPosition.xy/iResolution.xy;

            // Start our mixing variable at 1.0
            float lightAmount = 1.0;
            bool touched = false;

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
                if (shadowAmount < 1.0)
                {
                    if (touched == true)
                    {
                        lightAmount *= shadowAmount;
                    }
                    else
                    {
                        touched = true;
                    }
                }
                // lightAmount *= shadowAmount;
            }

            // Make shadow for terrain itself
            // float shadowAmount = terrain(normalizedFragCoord);
            // lightAmount *= shadowAmount;

            // float terrainUnmask = terrain(normalizedFragCoord);


            // Find out how much light we have based on the distance to our light
            lightAmount *= 1.0 - smoothstep(50, lightSize, distanceToLight);

            // smoothing edge of eye sight
            lightAmount *= 1.0 - smoothstep(0.5, radians(lightAngle), angleFromHeading);
            // We'll alternate our display between black and whatever is in channel 1
            vec4 blackColor = vec4(0.0, 0.0, 0.0, 1.0);

            // Our fragment color will be somewhere between black and channel 1
            // dependent on the value of b.
            vec4 ich1 = texture(iChannel1, normalizedFragCoord);
            float ich1_alpha = step(0.2, lightAmount);
            // ich1 = ich1 * ich1_alpha;

            fragColor = mix(blackColor, ich1, lightAmount);
        }
    }
    else
    {
        // vec2 samplep = fragCoord - lightPosition;

        // float angleFromHeading = acos(dot(samplep, lightDirectionV) / length(samplep));
        
        // mat2 rotate = mat2(
        //     cos(angleFromHeading), -sin(angleFromHeading),
        //     sin(angleFromHeading), cos(angleFromHeading)
        // );
        vec2 normalizedFragCoord = fragCoord/iResolution.xy;

        fragColor = texture(iChannel1, normalizedFragCoord);
    }
    
}
