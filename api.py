'''
>>> from tastekid.api import Similar
>>> s = Similar()
>>> r = s.query('yesman')
>>> r.movies
>>> r.music
>>> r.authors
>>> r.shows
>>> r.books
>>> m = r.movies[0].similar()
'''
    
import urllib
import urllib2
import json

class Utils(object):
    '''
    Utilities to assist in usage of the tastekid api.
    '''
    @staticmethod
    def clean(value):
        '''
        Fix issues with none ASCII text.
        TODO: Implement read of correct encoding format.
        '''
        try:
            return value.encode('UTF-8')
        except:
            return value
        

class Similar(object):
    '''
    Query tastekid for a similar nodelist
    '''
    _query = None
    _search = None
    _f = None
    _k = None
    type= None
    
    def __init__(self, search_value=None):
        if search_value:
            self.search = search_value
    
    def query(self, search_value=None, type='all', raw=False, f=None, k=None):
        '''
        Perform a query to tastekid. Passing a raw=True will return
        pure JSON code rather than the internal API class object
        '''
        if search_value == None and self.search == None:
            return AttributeError
        
        self._f = f
        self._k = k
        self.type = type
        
        if search_value:
            self.search = search_value
        
        if self._query == None:
            self._query = self._Query()
            self._query.type = self.type
            self._query.parent(self)
        
        data = self._query.get_data()
        
        if raw:
            return json.loads(data)
        else:
            return self._query.get_results(data)
    
    @property
    def search(self):
        ''' Add the query string to the class for mater use with 
        Similar.query() '''
        return self._search
    
    @search.setter
    def search(self, value):
        self._search = value
        
    
    class _Query(object):
        '''Internal query class - This should only be used through the 
        parent class Similar.query() '''
        _api_url = 'http://www.tastekid.com/ask/ws'
        _format = 'JSON'
        _verbose = False
        params = []
        _type = ''
        _parent = None
        
        @classmethod
        def _(self, value):
            '''wrapper for the Utils.clean() method - for cleaner look
            of the code'''
            return Utils.clean(value)
    
        
        def parent(self, parent):
            ''' Store a reference to the parent class internally'''
            self._parent = parent
            
        @property
        def type(self):
            ''' property for setting the type of results to receive'''
            return self._type
        
        @type.setter
        def type(self, value):
            '''books, movies, shows, music, authors, all, *'''
            value = value.lower()
            if value == '*' or value == 'all':
                value = ''
            else:
                value = '//' + str(value)
            self._type = value
        
        @property
        def request_url(self):
            '''
            Build the tastekid request URL
            '''
            q_plus = urllib.quote_plus(unicode(self._parent._search).encode('utf-8'))
            s = self._api_url + "?q=" + q_plus + self.type + \
            '&verbose=' + ('1' if self._verbose else '0') + '&format=' + self._format
            if self._parent._f:
                s = s + '&f=' + self._parent._f + '&k=' + self._parent._k
            return s
        
        def make_request(self):
            '''
            Perform the request to tastekid and return the 
            urllib2 reference
            '''
            req = urllib2.Request(self.request_url)
            r = urllib2.urlopen(req)
            return r
        
        def get_data(self):
            '''
            Read data from the request _Query.get_data()
            '''
            r = self.make_request()
            return r.read()
        
        def get_results(self, data=None):
            '''
            Parse the json result into the ResultNode class format
            '''
            l = []
            d = unicode(data, 'utf-8')
            if d:
                j = json.loads(d)
                s = j['Similar']['Info']
                r = j['Similar']['Results']
                source = ResultNode(self._(s[0]['Type']), self._(s[0]['Name']))
                for el in r:
                    node = ResultNode(self._(el['Type']), self._(el['Name']))
                    if self._verbose:
                        node.teaser = self._(el['wTeaser'])
                        node.wikipedia = self._(el['wUrl'])
                        node.youtube.id = self._(el['yID'])
                        node.youtube.title = self._(el['yTitle'])
                        node.youtube.url = self._(el['yUrl'])
                    l.append(node)
            return (source,ResultSet(l))

class ResultSet(object):
    '''
    A ResultSet is a wrapper for ResultNode objects.
    '''
    _nodes = None
    _type_list = []
    
    def __init__(self, nodes=None):
        if nodes:
            self.nodes = nodes
    
    @property
    def nodes(self):
        '''
        Return all results as a list of [<ResultNode>]
        '''
        return self._nodes
    
    @nodes.setter
    def nodes(self, value):
        '''
        Apply a node to the node list 
        - This property will also check to see if
        this object is already within the nodes list before
        appending.
        '''
        self._nodes = value
        self._type_list = []
        for n in value:
            if n.type not in self._type_list:
                self._type_list.append(n.type)
            
    
    def __len__(self):
        return len(self.nodes)
    
    def __getattr__(self,name=None):
        if name in self._type_list or name[:-1] in self._type_list:
            l = self.__getattr__('return_set')(name)
            if len(l) <= 0:
                l = self.__getattr__('return_set')(name[:-1])
            return l
        elif hasattr(self, name):
            return self.__getattribute__(name)
        else:
            return AttributeError
    
    @property
    def movies(self): return self.return_set('movie')
    
    @property
    def music(self): return self.return_set('music')
    
    @property
    def shows(self): return self.return_set('show')
    
    @property
    def books(self): return self.return_set('book')
    
    @property
    def authors(self): return self.return_set('author')
    
    def return_set(self,type):
        l = []
        for n in self._nodes:
            if n.type == type:
                l.append(n)
        return l
    

class ResultNode(object):
    '''
    ['type', 
    'name', 
    'teaser', 
    'wikipedia', 
    'youtube.id', 
    'youtube.title', 
    'youtube.url']
    '''
    
    type = None
    name = None
    teaser = None
    wikipedia = None
    _youtube = None
    
    def __init__(self, type=None, name=None):
        self._youtube = self.Youtube()
        if type:
            self.type = type
        if name:
            self.name = name
    
    def similar(self):
        s = Similar()
        return s.query(self.name)
    
    @property
    def youtube(self):
        return self._youtube
    
    @youtube.setter
    def youtube(self, val):
        self._youtube = val
    
    def __len__(self):
        return len(self.__list__())
    
    
    class Youtube(object):
        title = None
        id = None
        url = None
        
        def __repr__(self):
            return "<ResultNode:Youtube title:%s %s>" % (self.title, self.id)
        
        def __str__(self):
            return "%s - %s" % (self.title, self.id)
        
        def __unicode__(self):
            return "%s - %s" % (self.title, self.id)
    
    def __repr__(self):
        return "<ResultNode type:%s value:%s>" % (self.type, self.name)

    def __str__(self):
        return "%s - %s" % (self.type, self.value)
    
    def __unicode__(self):
        return "%s - %s" % (self.type, self.value)