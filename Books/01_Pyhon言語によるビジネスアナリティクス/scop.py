# scop interface module
# file name scop.py
# ver. 3.0 Copyright Log Opt Co., Ltd.
# by M. Kubo 2013, 2014, 2015
# 2015 5/1, 2018 5/21 (for both Mac for windows)
# define the path of the scop solver here:
SCOP = './scop.exe'
#SCOP = './bin/scop'
import sys
import copy
import platform

if int(sys.version_info[0])<=2:
    import string
    _trans = string.maketrans("-+*/'(){} ^=<>$&#?","_"*18)
else:
    _trans = str.maketrans("-+*/'(){} ^=<>$&#?","_"*18)

class Variable():
    """
    SCOP variable class. Variables are associated with a particular model.
    You can create a variable object by adding a variable to a model (using Model.addVariable or Model.addVariables)
    instead of by using a Variable constructor.
    """
    ID = 0 #variable ID for anonymous variables

    def __init__(self,name="",domain=[]):
        if name=="" or name==None:
            name ="__x{0}".format(Variable.ID)
            Variable.ID +=1
        #convert illegal characters into _ (underscore)
        self.name   = str(name).translate( _trans )
        #list(domain); domain name is converted to a string
        self.domain = [str(d) for d in domain]
        self.value  = None #optimal value

    def __str__(self):
        return "variable {0}:{1} = {2}".format(
            str(self.name), str(self.domain), str(self.value)
            )

class Parameters():
    """
    SCOP parameter class to control the operation of SCOP.

    TimeLimit: 	Limits the total time expended (in seconds). Positive integer. Default=600.
    OutputFlag: Controls the output log. Boolean. Default=False (0).
    RandomSeed: Sets the random seed number. Integer. Default=1.
    Target: Sets the target penalty value;
            optimization will terminate if the solver determines that the optimum penalty value
            for the model is worse than the specified "Target." Non-negative integer. Default=0.
    """
    def __init__(self):
        self.TimeLimit=600
        self.OutputFlag=0
        self.RandomSeed=1
        self.Target =0
        self.Initial=False

class Model(object):
    """
    SCOP model class.

    Attbibutes:
    constraints: Set of constraint objects in the model.
    variables: Set of variable objects in the model.
    Params:  Object including all the parameters of the model.
    varDict: Dictionary that maps variable names to the variable object.

    """
    def __init__(self,name=""):
        self.name = name
        self.constraints = [] # set of constraints is maintained by a list
        self.variables = []   # set of variables is maintained by a list
        self.Params=Parameters()
        self.varDict={}       # dictionary that maps variable names to their domains
        self.Status = 10      # unsolved
    def __str__(self):
        """
            return the information of the problem
            constraints are expanded and are shown in a readable format
        """
        ret = ["Model:"+str(self.name) ]
        ret.append( "number of variables = {0} ".format(len(self.variables)) )
        ret.append( "number of constraints= {0} ".format(len(self.constraints)) )
        for v in self.variables:
            ret.append(str(v))

        for c in self.constraints:
            ret.append("{0} :LHS ={1} ".format(str(c)[:-1], str(c.lhs)) )
        return " \n".join(ret)

    def update(self):
        """
        prepare a string representing the current model in the scop input format
        """
        f  = [ ]
        #variable declarations
        for var in self.variables:
            domainList = ",".join([str(i) for i in var.domain])
            f.append( "variable %s in { %s } \n" % (var.name, domainList) )
        #target value declaration
        f.append( "target = %s \n" % str(self.target) )
        #constraint declarations
        for con in self.constraints:
            f.append(str(con))
        return " ".join(f)

    def addVariable(self, name="", domain=[]):
        """
        addVariable ( name="", domain=[] )
        Add a variable to the model.

        Arguments:
        name: Name for new variable. A string object.
        domain: Domain (list of values) of new variable. Each value must be a string or numeric object.

        Return value:
        New variable object.

        Example usage:
        x = model.addVarriable("var")                     # domain  is set to []
        x = model.addVariable(name="var",domain=[1,2,3])  # arguments by name
        x = model.addVariable("var",["A","B","C"])        # arguments by position

        """
        var =Variable(name,domain)
        # keep variable names using the dictionary varDict
        # to check the validity of constraints later
        # check the duplicated name
        if var.name in self.varDict:
            raise ValueError("duplicate key '{0}' found in variable name".format(var.name))
        else:
            self.variables.append(var)
            self.varDict[var.name]=var
        return var

    def addVariables(self, names=[], domain=[]):
        """
        addVariables(names=[], domain=[])
        Add variables and their (identical) domain.

        Arguments:
        names: list of new variables. A list of string objects.
        domain: Domain (list of values) of new variables. Each value must be a string or numeric object.

        Return value:
        List of new variable objects.

        Example usage:
        varlist=["var1","var2","var3"]
        x = model.addVariables(varlist)                      # domain  is set to []
        x = model.addVariables(names=varlist,domain=[1,2,3]  # arguments by name
        x = model.addVariables(varlist,["A","B","C"]         # arguments by position

        """
        if type(names)!=type([]):
            raise TypeError("The first argument (names) must be a list.")
        varlist=[]
        for var in names:
            varlist.append(self.addVariable(var,domain))
        return varlist

    def addConstraint(self, con):
        """
        addConstraint ( con )
        Add a constraint to the model.

        Argument:
        con: A constraint object (Linear, Quadratic or AllDiff).

        Example usage:
        model.addConstraint(L)

        """
        if not isinstance(con,Constraint):
            raise TypeError("error: %r should be a subclass of Constraint" % con)

        #check the feasibility of the constraint added in the class con
        try:
            if con.feasible(self.varDict):
                self.constraints.append(con)
        except NameError:
            raise  NameError("Consrtaint %r has an error " % con )

##    def addConstraints(self,*cons):
##        for c in cons:
##            self.addConstraint(c)

    def optimize(self):
        """
        optimize ()
        Optimize the model using scop.exe in the same directory.

        Example usage:
        model.optimize()
        """

        time=self.Params.TimeLimit
        seed=self.Params.RandomSeed
        LOG=self.Params.OutputFlag
        self.target=self.Params.Target

        f = self.update()

        f3 = open("scop_input.txt","w")
        f3.write(f)
        f3.close()

        if LOG>=100:
            print("scop input: \n")
            print(f)
            print("\n")
        if LOG:
            print("solving using parameters: \n ")
            print("  TimeLimit =%s second \n"%time)
            print("  RandomSeed= %s \n"%seed)
            print("  OutputFlag= %s \n"%LOG)
        import subprocess
        if platform.system() == "Windows":
            cmd = "scop -time "+str(time)+" -seed "+str(seed) #solver call
        else:
            cmd = "./scop -time "+str(time)+" -seed "+str(seed) #solver call
                

        if self.Params.Initial:
            cmd += " -initsolfile scop_best_data.txt"

        try:
            if platform.system() == "Windows":
                pipe = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
            else:
                pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
            print("\n ================ Now solving the problem ================ \n")
            #pipe = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,stdin=subprocess.PIPE)
        except OSError:
            print("error: could not execute command '%s'" % cmd)
            print("please check that the solver is in the path")
            self.Status = 7  #execution falied
            return None, None

        out, err = pipe.communicate(f.encode()) #get the result
        if err!=None:
            if int(sys.version_info[0])>=3:
                err = str(err, encoding='utf-8')
            f2 = open("scop_error.txt","w")
            f2.write(err)
            f2.close()

        if int(sys.version_info[0])>=3:
            out = str(out, encoding='utf-8')

        if LOG:
            print (out, '\n')
        #print ("out=",out)
        #print ("err=",err)
        #print("Return Code=",pipe.returncode)

        f = open("scop_out.txt","w")
        f.write(out)
        f.close()

        #check the return code
        self.Status = pipe.returncode
        if self.Status !=0: #if the return code is not "optimal", then return
            print("Status=",self.Status)
            print("Output=",out)
            return None, None

        #extract the solution and the violated constraints
        s0 = "[best solution]"
        s1 = "penalty"
        s2 = "[Violated constraints]"
        i0 = out.find(s0) + len(s0)
        i1 = out.find(s1, i0)
        i2 = out.find(s2, i1) + len(s2)

        data = out[i0:i1].strip()

        #save the best solution
        f3 = open("scop_best_data.txt","w")
        f3.write(data.lstrip())
        f3.close()

        sol = {}
        if data != "":
            for s in data.split("\n"):
                name, value = s.split(":")
                sol[name]=value.strip() #remove redunant string

        data = out[i2:].strip()
        violated = {}
        if data != "":
            for s in data.split("\n"):
                try:
                    name, value = s.split(":")
                except:
                    print("Error String=",s)

                try:
                    temp=int(value)
                except:
                    violated[name] = value
                else:
                    violated[name] = int(value)

        #set the optimal solution to the variable
        for name in sol:
            if name in self.varDict:
                self.varDict[name].value = sol[name]
            else:
                raise NameError("Solution {0} is not in variable list".format(name))

        #evaluate the left hand sides of the constraints
        for con in self.constraints:

            if isinstance(con,Linear):
                lhs=0
                for (coeff,var,domain) in con.terms:
                    if var.value==domain:
                        lhs+=coeff

                con.lhs=lhs
            if isinstance(con,Quadratic):
                lhs=0
                #print con.terms
                for (coeff,var1,domain1,var2,domain2) in con.terms:
                    if var1.value==domain1 and var2.value==domain2:
                        lhs+=coeff

                con.lhs=lhs
            if isinstance(con,Alldiff):
                VarSet=set([])
                lhs=0
                for v in con.variables:
                    index=v.domain.index(v.value)
                    #print v,index
                    if index in VarSet:
                        lhs+=1
                    VarSet.add(index)
                #print VarSet
                con.lhs=lhs
        #return dictionaries containing the solution and the violated constraints
        return sol,violated


class Constraint(object):
    """
     Constraint base class
    """
    ID=0
    def __init__(self,name=None,weight=1):
        if name==None or name=="":
            name="__CON[{0}]".format(Constraint.ID)
            Constraint.ID+=1
        #convert illegal characters into _ (underscore)
        self.name   = str(name).translate( _trans )
        self.weight= str(weight)

    def setWeight(self,weight):
        self.weight = str(weight)


class Alldiff(Constraint):
    """
    Alldiff ( name=None,varlist=None,weight=1 )
    Alldiff type constraint constructor.

    Arguments:
    name: Name of all-different type constraint.
    varlist (optional): List of variables that must have differennt value indices.
    weight (optional): Positive integer representing importance of constraint.

    Attributes:
    name: Name of all-different type  constraint.
    varlist (optional): List of variables that must have differennt value indices.
    lhs: Left-hand-side constant of linear constraint.

    weight (optional): Positive integer representing importance of constraint.
    """
    def __init__(self,name=None,varlist=None,weight=1):
        #call the super class (Constraint) to initialize Alldiff
        super(Alldiff,self).__init__(name,weight)
        self.lhs=0
        if varlist==None:
            self.variables = set([])
        else:
            for var in varlist:
                if not isinstance(var,Variable):
                    raise NameError("error: %r should be a subclass of Variable" % var)
            self.variables = set(varlist)

    def __str__(self):
        """
        return the information of the alldiff constraint
        """
        f = [ "{0}: weight= {1} type=alldiff ".format(self.name,self.weight) ]
        for var in self.variables:
            f.append( var.name )
        f.append( "; \n" )
        return " ".join(f)

    def addVariable(self,var):
        """
        addVariable ( var )
        Add new variable into all-different type constraint.

        Arguments:
        var: Variable object added to all-different type constraint.

        Example usage:

        AD.addVaeiable( x )

        """
        if not isinstance(var,Variable):
            raise NameError("error: %r should be a subclass of Variable" % var)

        if var in self.variables:
            print("duplicate variable name error when adding variable %r" % var)
            return False
        self.variables.add(var)

    def addVariables(self, varlist):
        """
        addVariables ( varlist )
        Add variables into all-different type constraint.

        Arguments:
        varlist: List or tuple of variable objects added to all-different type constraint.

        Example usage:

        AD.addVariables( x, y, z )
        AD.addVariables( [x1,x2,x2] )

        """
        for var in varlist:
            self.addvar(var)

    def feasible(self,allvars):
        """
           return True if the constraint is defined correctly
        """
        for var in self.variables:
            if var.name not in allvars:
                raise NameError("no variable in the problem instance named %r" % var.name)
        return True


class Linear(Constraint):
    """
    Linear ( name, weight=1, rhs=0, direction="<=" )
    Linear constraint constructor.

    Arguments:
    name: Name of linear constraint.
    weight (optiona): Positive integer representing importance of constraint.
    rhs: Right-hand-side constant of linear constraint.
    direction: Rirection (or sense) of linear constraint; "<=" (default) or ">=" or "=".

    Attributes:
    name: Name of linear constraint.
    weight (optional): Positive integer representing importance of constraint.
    rhs: Right-hand-side constant of linear constraint.
    lhs: Left-hand-side constant of linear constraint.
    direction: Direction (or sense) of linear constraint; "<=" (default) or ">=" or "=".
    terms: List of terms in left-hand-side of constraint.
           Each term is a tuple of coeffcient,variable and its value.
    """
    def __init__(self,name=None,weight=1,rhs=0,direction="<="):
        """
        Constructor of linear constraint class:
        """
        super(Linear,self).__init__(name,weight)
        #self.name = name
        #self.weight = str(weight)
        self.rhs = rhs
        self.direction = direction
        self.terms = []
        self.lhs = 0

    def __str__(self):
        """ return the information of the linear constraint
            the constraint is expanded and is shown in a readable format
        """
        f =["{0}: weight= {1} type=linear".format(self.name, self.weight)]
        for (coeff,var,value) in self.terms:
            f.append( "{0}({1},{2})".format(str(coeff),var.name,str(value)) )
        f.append( self.direction+str(self.rhs) +"\n" )
        return " ".join(f)

    def addTerms(self,coeffs=[],vars=[],values=[]):
        """
        addTerms ( coeffs=[],vars=[],values=[] )
        Add new terms into left-hand-side of linear constraint.

        Arguments:
        coeffs: Coefficients for new terms; either a list of coefficients or a single coefficient.
                The three arguments must have the same size.
        vars: Variables for new terms; either a list of variables or a single variable.
                The three arguments must have the same size.
        values: Values for new terms; either a list of values or a single value.
                The three arguments must have the same size.

        Example usage:

        L.addTerms(1.0, y, "A")
        L.addTerms([2, 3, 1], [y, y, z], ["C", "D", "C"]) #2 X[y,"C"]+3 X[y,"D"]+1 X[z,"C"]

        """
        if type(coeffs) !=type([]): #need a check whether coeffs is numeric ...
            #arguments are nor list; add a term
            if type(coeffs)==type(1):
                self.terms.append( (coeffs,vars,str(values)))
        elif type(coeffs)!=type([]) or type(vars)!=type([]) or type(values)!=type([]):
            raise TypeError("coeffs, vars, values must be lists")
        elif len(coeffs)!=len(vars) or len(coeffs)!=len(values):
            raise TypeError("length of coeffs, vars, values must be identical")
        elif len(coeffs) !=len(vars) or len(coeffs) !=len(values):
            raise TypeError("error: length of coeffs, vars, and values must be identical")
        else:
            for i in range(len(coeffs)):
                self.terms.append( (coeffs[i],vars[i],str(values[i])))

    def setRhs(self,rhs=0):
        self.rhs = rhs

    def setDirection(self,direction="<="):
        if direction in ["<=",">=","="]:
            self.direction = direction
        else:
            raise NameError(
                "direction setting error; direction should be one of '<=', '>=', or '='"
                           )

    def feasible(self,allvars):
        """ return True if the constraint is defined correctly
        """
        for (coeff,var,value) in self.terms:
            if var.name not in allvars:
                raise NameError("no variable in the problem instance named %r" % var.name)
            if value not in allvars[var.name].domain:
                raise NameError("no value %r for the variable named %r" % (value, var.name))
        return True


class Quadratic(Constraint):
    """
    Quadratic ( name, weight=1, rhs=0, direction="<=" )
    Quadratic constraint constructor.

    Arguments:
    name: Name of quadratic constraint.
    weight (optional): Positive integer representing importance of constraint.
    rhs: Right-hand-side constant of linear constraint.
    direction: Direction (or sense) of linear constraint; "<=" (default) or ">=" or "=".

    Attributes:
    name: Name of quadratic constraint.
    weight (optiona): Positive integer representing importance of constraint.
    rhs: Right-hand-side constant of linear constraint.
    lhs: Left-hand-side constant of linear constraint.
    direction: Direction (or sense) of linear constraint; "<=" (default) or ">=" or "=".
    terms: List of terms in left-hand-side of constraint.
           each term is a tuple of coeffcient, variable1, value1, variable2 and value2.
    """

    def __init__(self,name=None,weight=1,rhs=0,direction="<="):
        super(Quadratic,self).__init__(name,weight)
        self.rhs = rhs
        self.direction = direction
        self.terms = []
        self.lhs =0

    def __str__(self):
        """ return the information of the quadratic constraint
            the constraint is expanded and is shown in a readable format
        """
        f = [ "{0}: weight={1} type=quadratic".format(self.name,self.weight) ]
        for (coeff,var1,value1,var2,value2) in self.terms:
            f.append( "{0}({1},{2})({3},{4})".format(
                str(coeff),var1.name,str(value1),var2.name,str(value2)
                ))
        f.append( self.direction+str(self.rhs) +"\n" )
        return " ".join(f)

    def addTerms(self,coeffs=[],vars=[],values=[],vars2=[],values2=[]):
        """
        addTerms ( coeffs=[],vars=[],values=[],vars2=[],values2=[])
        Add new terms into left-hand-side of qua
        dratic constraint.

        Arguments:
        coeffs: Coefficients for new terms; either a list of coefficients or a single coefficient.
                The five arguments must have the same size.
        vars: Variables for new terms; either a list of variables or a single variable.
                The five arguments must have the same size.
        values: Values for new terms; either a list of values or a single value.
                The five arguments must have the same size.
        vars2: Variables for new terms; either a list of variables or a single variable.
                The five arguments must have the same size.
        values2: Values for new terms; either a list of values or a single value.
                The five arguments must have the same size.
        Example usage:

        L.addTerms(1.0, y, "A", z, "B")
        L.addTerms([2, 3, 1], [y, y, z], ["C", "D", "C"], [x, x, y], ["A", "B", "C"])
                  #2 X[y,"C"] X[x,"A"]+3 X[y,"D"] X[x,"B"]+1 X[z,"C"] X[y,"C"]

        """
        if type(coeffs) !=type([]): #need a check whether coeffs is numeric ...
            self.terms.append( (coeffs,vars,str(values),vars2,str(values2)))
        elif type(coeffs)!=type([]) or type(vars)!=type([]) or type(values)!=type([]) \
             or type(vars2)!=type([]) or type(values2)!=type([]):
            raise TypeError("coeffs, vars, values must be lists")
        elif len(coeffs)!=len(vars) or len(coeffs)!=len(values) or len(values)!=len(vars) \
             or len(coeffs)!=len(vars2) or len(coeffs)!=len(values2):
            raise TypeError("length of coeffs, vars, values must be identical")
        else:
            for i in range(len(coeffs)):
                self.terms.append( (coeffs[i],vars[i],str(values[i]),vars2[i],str(values2[i])))

    def setRhs(self,rhs=0):
        self.rhs = rhs

    def setDirection(self,direction="<="):
        if direction in ["<=", ">=", "="]:
            self.direction = direction
        else:
            raise NameError(
                "direction setting error;direction should be one of '<=', '>=', or '='"
                  )

    def feasible(self,allvars):
        """
          return True if the constraint is defined correctly
        """
        for (coeff,var1,value1,var2,value2) in self.terms:
            if var1.name not in allvars:
                raise NameError("no variable in the problem instance named %r" % var1.name)
            if var2.name not in allvars:
                raise NameError("no variable in the problem instance named %r" % var2.name)
            if value1 not in allvars[var1.name].domain:
                raise NameError("no value %r for the variable named %r" % (value1, var1.name))
            if value2 not in allvars[var2.name].domain:
                raise NameError("no value %r for the variable named %r" % (value2, var2.name))
        return True

if __name__=="__main__":
##    m=Model("Assignment")
##    workers=["A++","B","C"]
##    Cost=[[15, 20, 30],[7, 15, 12],[25,10,13]]
##
##    varlist=m.addVariables(workers,range(3))
##
##    con1=Alldiff(varlist=varlist,weight="inf")
##    #con1=Alldiff("AD",varlist)
##    con1.setWeight("inf")
##    con2=Linear("",weight=1,rhs=0,direction="<=")
##    for i in range(len(workers)):
##        for j in range(3):
##            con2.addTerms(Cost[i][j],varlist[i],j)
##    m.addConstraint(con1)
##    m.addConstraint(con2)
##    m.Params.TimeLimit=1

    m=Model()
    workers=["A","B","C","D","E"]
    #workers=["A+","A**","","","A(0)"] #anonymous name
    Cost=[[15, 20, 30],[7, 15, 12],[25,10,13],[15,18,3],[5,12,17]]
    LB=[1,2,2]
    JOB=["Job1","Job2","Job3"]
    varlist=m.addVariables(workers,JOB)

    con0=Alldiff(varlist=varlist,weight="inf")
    m.addConstraint(con0)

    LBC={} #dictionary for keeping lower bound constraints
    for j in range(len(LB)):
        LBC[j]=Linear("LB%s"%j,"inf",LB[j],">=")
        for i in range(len(workers)):
             LBC[j].addTerms(1,varlist[i],JOB[j])
        m.addConstraint(LBC[j])

    con1=Linear("L")
    for i in range(len(workers)):
        for j,task in enumerate(JOB):
            con1.addTerms(Cost[i][j],varlist[i],task)
    m.addConstraint(con1)
##
##    #Method 1: by calling addTerms just once
##    ##    coeffs=[1,1,1]
##    ##    var1=[varlist[0],varlist[0],varlist[0]]
##    ##    var2=[varlist[2],varlist[2],varlist[2]]
##    ##    vallist=[0,1,2]
##    ##    vallist2=[0,1,2]
##    ##    con2=Quadratic("quadratic_constraint",100)
##    ##    con2.addTerms(coeffs,var1,vallist,var2,vallist2)
##
    #Method 2: using addTerms to add terms one by one (recommendation)
    con2=Quadratic("Q",100)
    for j in JOB:
        con2.addTerms(1,varlist[0],j,varlist[2],j)

    #con2.addTerms(1,varlist[0],1,varlist[0],1)
    #con2.addTerms(1,varlist[0],2,varlist[0],2)
    #con2.addTerms(1,varlist[0],0,varlist[0],0)

    m.addConstraint(con2)

    m.Params.TimeLimit=1
    #m.Params.Initial =True

    sol,violated=m.optimize()

    #print m

    print ("constraint",con1)
    print ("lhs",con1.lhs)

    print ("constraint",con2)
    print ("lhs",con2.lhs)

    print ("solution")
    for x in sol:
        print (x,sol[x])
    print ("violated constraint(s)")
    for v in violated:
        print (v,violated[v])
##
##    m=Model()
##    Type=["A","B","C","D"] #car types
##    Number=[30,30,20,40]   #number of cars needed
##    n=sum(Number) #planning horizon
##    #1st line produces car type B and C that has a workplace with length 5 and 3 workers
##    #2nd line produces car type A anc C that has a workplace with length 3 and 2 workers
##    Need=[["B","C"],["A","C"]]
##    Length=[5,3]
##    Capacity=[3,2]
##
##    x={}
##    for i in range(n):
##        x[i]=m.addVariable("seq[%s]"%i,Type)
##
##    #production volume constraints
##    for i in range(len(Type)):
##        L1=Linear("req[%s]"%i,direction="=",rhs=Number[i])
##        for j in range(n):
##            L1.addTerms(1,x[j],Type[i])
##        m.addConstraint(L1)
##
##    for i in range(len(Length)):
##        for k in range(n-Length[i]+1):
##            L2=Linear("ub[%s_%s]"%(i,k),direction="<=",rhs=Capacity[i])
##            for t in range(k,k+Length[i]):
##                for j in range(len(Need[i])):
##                    L2.addTerms(1,x[t],Need[i][j])
##            m.addConstraint(L2)
##
##    m.Params.TimeLimit=1
##    m.Params.OutputFlag=False
##    sol,violated=m.optimize()
##
##    print "solution"
##    for x in sol:
##        print x,sol[x]
##    print "violated constraint(s)"
##    for v in violated:
##        print v,violated[v]

