"""
Vector class for any purpose
by joonhyuk@me.com

forked from https://gist.github.com/mcleonard/5351452
"""
import math
from typing import Iterable

def _check_valid_iterable(other) -> bool:
    if isinstance(other, Vector):
        return True
    if isinstance(other, (tuple, list, set, Iterable)):
        """ Validity check for elements(below line) will be on the fly for performance """
        # assert all(isinstance(x, (float, int)) for x in other), f'Invalid vector object : {other}'
        return True
    return False
    

class Vector(tuple):
    
    def __new__(cls, *args):
        if not args:
            args = (0, 0)
        elif len(args) == 1:
            if _check_valid_iterable(args[0]):
                args = args[0]
            else: raise ValueError("Single argument should be tuple | list | Vector")
        return tuple.__new__(cls, args)
    
    def norm(self):
        """ Returns the norm (length, magnitude) of the vector """
        return math.sqrt(sum( x*x for x in self ))
        
    def argument(self, origin=None, radians=False):
        """ Returns the argument of the vector, the angle clockwise from +x. In degress by default, 
            set radians=True to get the result in radians. This only works for 2D vectors. """
        if origin is None: origin = vector_right
        norm = self.norm()
        if not norm: return 0
        arg_in_rad = math.acos(origin*self/norm)
        if radians:
            return arg_in_rad
        arg_in_deg = math.degrees(arg_in_rad)
        if self[1] < 0: 
            return 360 - arg_in_deg
        else: 
            return arg_in_deg

    @property
    def angle(self):
        """ Returns the argument of the vector, with degrees, origin of (1, 0), clockwise
        
        For slightly better performance than argument() """
        norm = math.sqrt(sum( x*x for x in self ))
        if not norm: return 0
        angle = math.degrees(math.acos(vector_right * self/norm))
        if self[1] < 0:
            return 360 - angle
        else:
            return angle
    
    def normalize(self):
        """ Returns a normalized unit vector """
        norm = self.norm()
        if norm == 1.0: return self
        if norm == 0.0: return self.__class__(0.,0.)
        normed = tuple( x / norm for x in self )
        return self.__class__(*normed)
    
    def rotate(self, theta, radian = False):
        """ Rotate this vector. If passed a number, assumes this is a 
            2D vector and rotates by the passed value in degrees.  Otherwise,
            assumes the passed value is a list acting as a matrix which rotates the vector.
        """
        if isinstance(theta, (int, float)):
            # So, if rotate is passed an int or a float...
            if len(self) != 2:
                raise ValueError("Rotation axis not defined for greater than 2D vector")
            if radian: return self._rotate2D_radian(theta)
            else: return self._rotate2D(theta)
        
        matrix = theta
        if not all(len(row) == len(self) for row in matrix) or not len(matrix)==len(self):
            raise ValueError("Rotation matrix must be square and same dimensions as vector")
        return self.matrix_mult(matrix)
    
    def _rotate2D_radian(self, theta):
        # Just applying the 2D rotation matrix
        dc, ds = math.cos(theta), math.sin(theta)
        x, y = self
        x, y = dc*x - ds*y, ds*x + dc*y
        return self.__class__(x, y)
    
    def _rotate2D(self, theta):
        """ Rotate this vector by theta in degrees.
            
            Returns a new vector.
        """
        theta = math.radians(theta)
        # Just applying the 2D rotation matrix
        dc, ds = math.cos(theta), math.sin(theta)
        x, y = self
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
    
    def inner(self, other):
        """ Returns the dot product (inner product) of self and another vector
        """
        if not _check_valid_iterable(other):
            raise ValueError('The dot product requires another vector')
        return sum(a * b for a, b in zip(self, other))
    
    def __hash__(self) -> int:
        return super().__hash__()
    
    def __mul__(self, other):
        """ Returns the dot product of self and other if multiplied
            by another Vector.  If multiplied by an int or float,
            multiplies each component by other.
        """
        if _check_valid_iterable(other):
            return self.inner(other)
        elif isinstance(other, (int, float)):
            product = tuple( a * other for a in self )
            return self.__class__(*product)
        else:
            raise ValueError("Multiplication with type {} not supported".format(type(other)))
    
    def __rmul__(self, other):
        """ Called if 4 * self for instance """
        return self.__mul__(other)
    
    def __imul__(self, other):
        return self.__mul__(other)
    
    def __neg__(self):
        return self.__mul__(-1)
    
    def __truediv__(self, other):
        if _check_valid_iterable(other):
            divided = tuple( a / b for a, b in zip(self, other))
        elif isinstance(other, (int, float)):
            divided = tuple( a / other for a in self )
        else:
            raise ValueError("Division with type {} not supported".format(type(other)))
        
        return self.__class__(*divided)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __floordiv__(self, other):
        if _check_valid_iterable(other):
            # divided = tuple(self[i] / other[i] for i in range(len(self)))
            divided = tuple( a // b for a, b in zip(self, other))
        elif isinstance(other, (int, float)):
            divided = tuple( a // other for a in self )
        else:
            raise ValueError("Division with type {} not supported".format(type(other)))
        
        return self.__class__(*divided)

    def __ifloordiv__(self, other):
        return self.__floordiv__(other)

    def __add__(self, other):
        """ Returns the vector addition of self and other """
        if _check_valid_iterable(other):
            added = tuple( a + b for a, b in zip(self, other) )
        elif isinstance(other, (int, float)):
            added = tuple( a + other for a in self )
        else:
            raise ValueError("Addition with type {} not supported".format(type(other)))
        return self.__class__(*added)
    
    def __radd__(self, other):
        """ Called if 4 + self for instance """
        return self.__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        """ Returns the vector difference of self and other """
        if other is None: return self
        if _check_valid_iterable(other):
            subbed = tuple( a - b for a, b in zip(self, other) )
        elif isinstance(other, (int, float)):
            subbed = tuple( a - other for a in self )
        else:
            raise ValueError("Subtraction with type {} not supported".format(type(other)))
        
        return self.__class__(*subbed)
    
    def __rsub__(self, other):
        """ Called if 4 - self for instance """
        return self.__sub__(other)
    
    def __isub__(self, other):
        return self.__sub__(other)

    def __eq__(self, other):
        if _check_valid_iterable(other):
            return all(a == b for a, b in zip(self, other))
        else:
            return False
            # raise ValueError("Comparison with type {} not supported".format(type(other)))
    
    def __lt__(self, other):
        if _check_valid_iterable(other):
            return all(a < b for a, b in zip(self, other))
        else:
            return False
    
    def __le__(self, other):
        if _check_valid_iterable(other):
            return all(a <= b for a, b in zip(self, other))
        else:
            return False
    
    def __round__(self, ndigits = None):
        ndigits_list = [ndigits] * self.__len__()
        rounded = tuple(map(round, self, ndigits_list))
        return self.__class__(*rounded)

    def __pow__(self, n):
        '''The operator pow overloaded. You can powering vectors writing
         V ** n, where V is a vector, and n is the power. If V = (a, b), then
         V ** n calculates (a ** n, b ** n)'''
        powered = tuple(a ** n for a in self)
        return self.__class__(*powered)

    def __ipow__(self, other):
        return self.__pow__(other)

    @property
    def ceil(self):
        rounded = tuple(map(math.ceil, self))
        return self.__class__(*rounded)
    
    @property
    def floor(self):
        rounded = tuple(map(math.floor, self))
        return self.__class__(*rounded)
    
    def clamp_max(self, other):
        clamped = tuple(map(min, self, other))
        return clamped
    
    def clamp_min(self, other):
        clamped = tuple(map(max, self, other))
        return clamped
    
    def clamp(self, min, max):
        return self.clamp_min(self.clamp_max(max), min)
    
    def clamp_length(self, max_length:float = 1.0):
        norm = self.norm()
        if norm <= max_length: return self
        clamped = tuple( x * max_length / norm for x in self )
        return self.__class__(*clamped)
    
    def is_close(self, other, precision = 0.001):
        ''' check if nearly equality '''
        if self == other: return True
        if not _check_valid_iterable(other):
            raise ValueError('nearly_equal requires another vector')
        ''' 차원 수 비교체크는 성능상 생략 '''
        result = all(math.isclose(a, b, abs_tol = precision) for a, b in zip(self, other))
        # if result:
            # self.values = other.values # 소용 없음...
        return result

    @classmethod
    def diagonal(cls, value, dimension = 2):
        """simple way to make vector from one value"""
        va = [value] * dimension
        return cls(va)
    
    @classmethod
    def directional(cls, angle = 0):
        theta = math.radians(angle)
        return cls(math.cos(theta), math.sin(theta))
    
    @property
    def unit(self):
        ''' return unit vector'''
        return self.normalize()
    
    @property
    def is_zero(self) -> bool:
        return self.length == 0.0
    
    # @property
    def near_zero(self, precision = 0.01) -> bool:
        length = math.sqrt(sum( x*x for x in self ))
        if not length : return True
        return math.isclose(length, 0, abs_tol = precision)
    
    @property
    def length(self):
        return math.sqrt(sum( x*x for x in self ))
    
    @property
    def x(self):
        """get first value of Vector
        for better usability, by mash"""
        return self[0]
    
    @property
    def y(self):
        """get second value of Vector
        for better usability, by mash"""
        return self[1]
    
    @property
    def z(self):
        """get third value of Vector, if exists
        for better usability, by mash"""
        if self.__len__ > 2:
            return self[2]
        else:
            return None

vector_zero = Vector(0, 0)
vector_right = Vector(1, 0)
vector_up = Vector(0, 1)


if __name__ != "__main__":
    print("include", __name__, ":", __file__)
else:
    v = Vector()
    print(type(v))
    