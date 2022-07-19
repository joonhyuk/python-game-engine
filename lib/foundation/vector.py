"""
Vector class for any purpose
by joonhyuk@me.com

forked from https://gist.github.com/mcleonard/5351452
"""
import math

class Vector(object):
    def __init__(self, *args):
        """ Create a vector, example: v = Vector(1,2) """
        if not args : self.values = (0.,0.)
        elif len(args) == 1:  # add more usability and risk...!
            if isinstance(args[0], (tuple, list, Vector)):
                self.values = tuple(args[0])
            else: raise ValueError("Single argument should be tuple | list | Vector")
        else: self.values = args
        # self.is_zero:bool = self.norm()
        
    def norm(self):
        """ Returns the norm (length, magnitude) of the vector """
        return math.sqrt(sum( x*x for x in self ))
    
    @property
    def length(self):
        return self.norm()
        
    def argument(self, radians=False):
        """ Returns the argument of the vector, the angle clockwise from +y. In degress by default, 
            set radians=True to get the result in radians. This only works for 2D vectors. """
        arg_in_rad = math.acos(Vector(0, 1)*self/self.norm())
        if radians:
            return arg_in_rad
        arg_in_deg = math.degrees(arg_in_rad)
        if self.values[0] < 0: 
            return 360 - arg_in_deg
        else: 
            return arg_in_deg

    def normalize(self):
        """ Returns a normalized unit vector """
        norm = self.norm()
        if norm == 1.0: return self
        normed = tuple( x / norm for x in self )
        return self.__class__(*normed)
    
    def rotate(self, theta):
        """ Rotate this vector. If passed a number, assumes this is a 
            2D vector and rotates by the passed value in degrees.  Otherwise,
            assumes the passed value is a list acting as a matrix which rotates the vector.
        """
        if isinstance(theta, (int, float)):
            # So, if rotate is passed an int or a float...
            if len(self) != 2:
                raise ValueError("Rotation axis not defined for greater than 2D vector")
            return self._rotate2D(theta)
        
        matrix = theta
        if not all(len(row) == len(self) for row in matrix) or not len(matrix)==len(self):
            raise ValueError("Rotation matrix must be square and same dimensions as vector")
        return self.matrix_mult(matrix)
        
    def _rotate2D(self, theta):
        """ Rotate this vector by theta in degrees.
            
            Returns a new vector.
        """
        theta = math.radians(theta)
        # Just applying the 2D rotation matrix
        dc, ds = math.cos(theta), math.sin(theta)
        x, y = self.values
        x, y = dc*x - ds*y, ds*x + dc*y
        return self.__class__(x, y)
        
    def matrix_mult(self, matrix):
        """ Multiply this vector by a matrix.  Assuming matrix is a list of lists.
        
            Example:
            mat = [[1,2,3],[-1,0,1],[3,4,5]]
            Vector(1,2,3).matrix_mult(mat) ->  (14, 2, 26)
        
        """
        if not all(len(row) == len(self) for row in matrix):
            raise ValueError('Matrix must match vector dimensions') 
        
        # Grab a row from the matrix, make it a Vector, take the dot product, 
        # and store it as the first component
        product = tuple(Vector(*row)*self for row in matrix)
        
        return self.__class__(*product)
    
    def inner(self, vector):
        """ Returns the dot product (inner product) of self and another vector
        """
        if not isinstance(vector, Vector):
            raise ValueError('The dot product requires another vector')
        return sum(a * b for a, b in zip(self, vector))
    
    def __mul__(self, other):
        """ Returns the dot product of self and other if multiplied
            by another Vector.  If multiplied by an int or float,
            multiplies each component by other.
        """
        if isinstance(other, Vector):
            return self.inner(other)
        elif isinstance(other, (int, float)):
            product = tuple( a * other for a in self )
            return self.__class__(*product)
        else:
            raise ValueError("Multiplication with type {} not supported".format(type(other)))
    
    def __rmul__(self, other):
        """ Called if 4 * self for instance """
        return self.__mul__(other)
    
    def __neg__(self):
        return self.__mul__(-1)
    
    def __truediv__(self, other):
        if isinstance(other, Vector):
            divided = tuple(self[i] / other[i] for i in range(len(self)))
        elif isinstance(other, (int, float)):
            divided = tuple( a / other for a in self )
        else:
            raise ValueError("Division with type {} not supported".format(type(other)))
        
        return self.__class__(*divided)
    
    def __add__(self, other):
        """ Returns the vector addition of self and other """
        if isinstance(other, (Vector, tuple, list)):
            added = tuple( a + b for a, b in zip(self, other) )
        elif isinstance(other, (int, float)):
            added = tuple( a + other for a in self )
        else:
            raise ValueError("Addition with type {} not supported".format(type(other)))
        
        return self.__class__(*added)

    def __radd__(self, other):
        """ Called if 4 + self for instance """
        return self.__add__(other)
    
    def __sub__(self, other):
        """ Returns the vector difference of self and other """
        if isinstance(other, (Vector, tuple, list)):
            subbed = tuple( a - b for a, b in zip(self, other) )
        elif isinstance(other, (int, float)):
            subbed = tuple( a - other for a in self )
        else:
            raise ValueError("Subtraction with type {} not supported".format(type(other)))
        
        return self.__class__(*subbed)
    
    def __rsub__(self, other):
        """ Called if 4 - self for instance """
        return self.__sub__(other)
    
    def __iter__(self):
        return self.values.__iter__()
    
    def __len__(self):
        return len(self.values)
    
    def __getitem__(self, key):
        return self.values[key]
        
    def __repr__(self):
        return str(self.values)

    def __eq__(self, other):
        if isinstance(other, Vector):
            return all(a == b for a, b in zip(self, other))
        else:
            return False
            # raise ValueError("Comparison with type {} not supported".format(type(other)))
        
    def __round__(self, ndigits = None):
        ndigits_list = [ndigits] * self.__len__()
        rounded = tuple(map(round, self.values, ndigits_list))
        return self.__class__(*rounded)
    
    @property
    def ceil(self):
        rounded = tuple(map(math.ceil, self.values))
        return self.__class__(*rounded)
    
    @property
    def floor(self):
        rounded = tuple(map(math.floor, self.values))
        return self.__class__(*rounded)
    
    def clamp_max(self, other):
        """return claped vector"""
        clamped = tuple(map(min, self.values, other))
        return clamped
        # return self.__class__(min(other[0], self.x), min(other[1], self.y))
    
    def clamp_length(self, max_length:float = 1.0):
        norm = self.norm()
        if norm <= max_length: return self
        clamped = tuple( x * max_length / norm for x in self )
        return self.__class__(*clamped)
    
    def is_close(self, other, precision = 0.001):
        ''' check if nearly equality '''
        if self == other: return True
        if not isinstance(other, Vector): 
            raise ValueError('nearly_equal requires another vector')
        ''' 차원 수 비교체크는 성능상 생략 '''
        result = all(math.isclose(a, b, abs_tol = precision) for a, b in zip(self, other))
        # if result:
            # self.values = other.values # 소용 없음...
        return result
        
    # def __sum__(self, *others):
    #     pass
    # no need for it. yay!
    
    @classmethod
    def diagonal(cls, value, dimension = 2):
        """simple way to make vector from one value"""
        va = [value] * dimension
        return cls(va)
    
    @property
    def unit(self):
        return self.normalize()
    
    @property
    def is_zero(self) -> bool:
        return self.norm() == 0.0
    
    @property
    def near_zero(self) -> bool:
        length = self.norm()
        if length == 0.0 : return True
        return math.isclose(length, 0, abs_tol = 0.01)
    
    @property
    def x(self):
        """get first value of Vector
        for better usability, by mash"""
        return self.values[0]
    
    @property
    def y(self):
        """get second value of Vector
        for better usability, by mash"""
        return self.values[1]
    
    @property
    def z(self):
        """get third value of Vector, if exists
        for better usability, by mash"""
        if self.values.__len__ > 2:
            return self.values[2]
        else:
            return None
    
    @x.setter
    def x(self, value):
        """set first value of Vector
        for better usability, by mash"""
        if isinstance(value, (int, float)):
            values = list(self.values)
            values[0] = value
            self.values = tuple(values)
        else:
            raise ValueError("Set with type {} not supported".format(type(value)))
    
    @y.setter
    def y(self, value):
        """set second value of Vector
        for better usability, by mash"""
        if isinstance(value, (int, float)):
            values = list(self.values)
            values[1] = value
            self.values = tuple(values)
        else:
            raise ValueError("Set with type {} not supported".format(type(value)))
    
    @z.setter
    def z(self, value):
        """set third value of Vector, if exists
        for better usability, by mash"""
        if self.values.__len__ < 3: return False
        if isinstance(value, (int, float)):
            values = list(self.values)
            values[3] = value
            self.values = tuple(values)
        else:
            raise ValueError("Set with type {} not supported".format(type(value)))

if __name__ != "__main__":
    print("include", __name__, ":", __file__)
else:
    v1 = Vector()
    v2 = Vector(0.001, -0.0011)
    print(v2.is_close(v1))
    