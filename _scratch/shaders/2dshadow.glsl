// learning turotial 3 shadows and light in 2D !

// 2d shadow based on https://www.shadertoy.com/view/XdjGDm by @DiLemming
// same structure but different functions implementation.

// click to move the circle

#define STEPS 10.
#define  PI 3.1415926;
#define SCALE 1000.


struct ray {
	vec2 o;
	vec2 d;
	vec2 t;
};

mat2 R2(float t) {
    float s = sin(t);
    float c = cos(t);
    return mat2(c,  -s, s, c);

}



float square(vec2 p, vec2 pos, float sz) {
	vec2 q = p - pos ;
    q = R2(iTime)*q;
    float f = max(q.x*q.x , q.y*q.y ) / sz;
    return f;
}
float circle(vec2 p, vec2 pos, float sz) {
    vec2 q = p - pos ;
    return dot (q, q)  / sz ;
}


float scene (in vec2 p) {

    vec2 m = (iMouse.xy - 0.5 * iResolution.xy) / iResolution.y;
	vec2 cpos = m.xy ;
    float teta = atan(m.y,m.x );
    vec2 spos = vec2 (.3*sin(.7*iTime)+.1,.2*cos(.3*iTime)+.2) ;
    spos = R2(.9*iTime+ .3)*spos;
    float c = circle(p,cpos,3.+ 1.*cos(teta*30.+ iTime));
    float f = square(p, spos, 2.);
	f = min (f, c ) * SCALE;
	return exp(-.5*f)/(f + 1.);
}

ray make_ray (in vec2 origin, in vec2 target) {
	ray r;

	r.o = origin;
	r.d = (target - origin) / STEPS;
	r.t = target;

	return r;
}

void march (inout ray r) {
    for (float i = 0.; i < 1.; i += .5/STEPS) {
        float f = scene (r.o);
        f = .2* pow((1. + f*f), -10.) ;
        r.o += f * r.d;
    }
    r.o -= r.t ;

}

vec3 light (in ray r, in vec3 color) {
    float d = dot (r.o, r.o);
	//vec3 col =   color / (5.5* d + 1.5*color);
	vec3 col =   .1*color*exp(2./(1.5*d + 3.*color));
    return col;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;
    vec3 col = vec3(0.);
	ray r0 = make_ray (uv, vec2 (.7, .8));
    march(r0);
    vec3 sun = light (r0, vec3 (0.6, 0.2, 0.1) );
	//ray r1 = make_ray (uv, vec2 (-1., 1.));
    //march(r1);
    //sun += light (r1, vec3 (0.3, 0.2, 0.6) );
    col += sun;
	float f = clamp( 1000.*scene(uv)-500.,1.,10.)  ;
    col.r *= f;
    col = pow(col, vec3(0.4545)); // gamma correction
	fragColor = vec4 (col,1.);
}
