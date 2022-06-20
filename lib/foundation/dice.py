import random, re

class Dice:
    def __init__(self, faces = range(1, 7), rolls = 1, sum_results_if_int = True, bonus_if_int = 0) -> None:
        self.face = None
        self.faces = None
        self.sum_result = sum_results_if_int
        self.int_bonus = bonus_if_int
        
        if rolls > 1 and not all(isinstance(e, int) for e in faces):
            raise ValueError('Faces must me int type if rolls > 1')
        
        self.rolls = rolls
        self.set_faces(faces)
    
    def set_faces(self, faces):
        try:
            self.len = len(faces)
        except:
            raise ValueError('Faces must be a sequence like tuple, list, dict')
        if self.len < 2:
            raise ValueError('The dice must have at least 2 sides.')
        self.faces = faces
        self.roll()
    
    def roll(self, rolls = None, int_bonus = None):
        if not rolls: rolls = self.rolls
        if not int_bonus: int_bonus = self.int_bonus
        
        results = []
        
        for _ in range(rolls):
            if isinstance(self.faces, dict):
                results.append(self.faces[random.choice(list(self.faces.keys()))])
            else:
                results.append(random.choice(self.faces))
        
        if self.sum_result and all(isinstance(e, int) for e in results):
            self.face = sum(results) + int_bonus
        else: self.face = results
        
        return self.face
    
    @classmethod
    def coin(cls):
        return cls((True, False))
    
    @classmethod
    def dx(cls, abbr:str = '1d6'):
        '''
        D&D style dice expression
        examples : 1d6, d20, 2d8-1, d64+1
        '''
        if not re.search('^[0-9]*[dD][0-9]*([\+-]{1,1}[0-9]+)?$', abbr):
            raise AttributeError(f'Invalid dice expression : {abbr}')
        s1 = re.split('\+|-', abbr)
        
        if len(s1) == 1 or s1[1] is '':
            bonus = 0
        else:
            bonus = int(s1[1])
            if re.findall('\+|-', abbr)[0] == '-': bonus *= -1
        
        s2 = re.split('d|D', s1[0])
        
        if s2[0] == '': rolls = 1
        else: rolls = int(s2[0])
        
        if int(s2[1]) < 2: raise ValueError('Number of face must be >= 2')
        else: faces = int(s2[1]) + 1
        
        return cls(faces = range(1, faces),
                   rolls = rolls, 
                   bonus_if_int = bonus)
    
    @property
    def new_face(self):
        '''roll and return face'''
        self.roll()
        return self.face
