import re
import sys
import threading
import threadinglocal

if sys.version < '2.4':
    from sets import ImmutableSet as frozenset

from routes import request_config
from routes.util import controller_scan, RouteException
from routes.route import Route


def strip_slashes(name):
    """Remove slashes from the beginning and end of a part/URL."""
    if name.startswith('/'):
        name = name[1:]
    if name.endswith('/'):
        name = name[:-1]
    return name


class Mapper(object):
    """Mapper handles URL generation and URL recognition in a web
    application.
    
    Mapper is built handling dictionary's. It is assumed that the web
    application will handle the dictionary returned by URL recognition
    to dispatch appropriately.
    
    URL generation is done by passing keyword parameters into the
    generate function, a URL is then returned.
    
    """
    def __init__(self, controller_scan=controller_scan, directory=None, 
                 always_scan=False, register=True, explicit=False):
        """Create a new Mapper instance
        
        All keyword arguments are optional.
        
        ``controller_scan``
            Function reference that will be used to return a list of
            valid controllers used during URL matching. If
            ``directory`` keyword arg is present, it will be passed
            into the function during its call. This option defaults to
            a function that will scan a directory for controllers.
        
        ``directory``
            Passed into controller_scan for the directory to scan. It
            should be an absolute path if using the default 
            ``controller_scan`` function.
        
        ``always_scan``
            Whether or not the ``controller_scan`` function should be
            run during every URL match. This is typically a good idea
            during development so the server won't need to be restarted
            anytime a controller is added.
        
        ``register``
            Boolean used to determine if the Mapper should use 
            ``request_config`` to register itself as the mapper. Since
            it's done on a thread-local basis, this is typically best
            used during testing though it won't hurt in other cases.
        
        ``explicit``
            Boolean used to determine if routes should be connected
            with implicit defaults of::
                
                {'controller':'content','action':'index','id':None}
            
            When set to True, these defaults will not be added to route
            connections and ``url_for`` will not use Route memory.
                
        Additional attributes that may be set after mapper
        initialization (ie, map.ATTRIBUTE = 'something'):
        
        ``encoding``
            Used to indicate alternative encoding/decoding systems to
            use with both incoming URL's, and during Route generation
            when passed a Unicode string. Defaults to 'utf-8'.
        
        ``decode_errors``
            How to handle errors in the encoding, generally ignoring
            any chars that don't convert should be sufficient. Defaults
            to 'ignore'.
        
        ``minimization``
            Boolean used to indicate whether or not Routes should
            minimize URL's and the generated URL's, or require every
            part where it appears in the path. Defaults to True.
        
        ``hardcode_names``
            Whether or not Named Routes result in the default options
            for the route being used *or* if they actually force url
            generation to use the route. Defaults to False.
        
        """
        self.matchlist = []
        self.maxkeys = {}
        self.minkeys = {}
        self.urlcache = {}
        self._created_regs = False
        self._created_gens = False
        self.prefix = None
        self.req_data = threadinglocal.local()
        self.directory = directory
        self.always_scan = always_scan
        self.controller_scan = controller_scan
        self._regprefix = None
        self._routenames = {}
        self.debug = False
        self.append_slash = False
        self.sub_domains = False
        self.sub_domains_ignore = []
        self.domain_match = '[^\.\/]+?\.[^\.\/]+'
        self.explicit = explicit
        self.encoding = 'utf-8'
        self.decode_errors = 'ignore'
        self.hardcode_names = True
        self.minimization = True
        self.create_regs_lock = threading.Lock()
        if register:
            config = request_config()
            config.mapper = self
    
    def _envget(self):
        return getattr(self.req_data, 'environ', None)
    def _envset(self, env):
        self.req_data.environ = env
    def _envdel(self):
        del self.req_data.environ
    environ = property(_envget, _envset, _envdel)

    def connect(self, *args, **kargs):
        """Create and connect a new Route to the Mapper.
        
        Usage:
        
        .. code-block:: python
        
            m = Mapper()
            m.connect(':controller/:action/:id')
            m.connect('date/:year/:month/:day', controller="blog", action="view")
            m.connect('archives/:page', controller="blog", action="by_page",
            requirements = { 'page':'\d{1,2}' })
            m.connect('category_list', 'archives/category/:section', controller='blog', action='category',
            section='home', type='list')
            m.connect('home', '', controller='blog', action='view', section='home')
        
        """
        routename = None
        if len(args) > 1:
            routename = args[0]
            args = args[1:]
        if '_explicit' not in kargs:
            kargs['_explicit'] = self.explicit
        if '_minimize' not in kargs:
            kargs['_minimize'] = self.minimization
        route = Route(*args, **kargs)
                
        # Apply encoding and errors if its not the defaults and the route 
        # didn't have one passed in.
        if (self.encoding != 'utf-8' or self.decode_errors != 'ignore') and \
           '_encoding' not in kargs:
            route.encoding = self.encoding
            route.decode_errors = self.decode_errors
        
        self.matchlist.append(route)
        if routename:
            self._routenames[routename] = route
        if route.static:
            return
        exists = False
        for key in self.maxkeys:
            if key == route.maxkeys:
                self.maxkeys[key].append(route)
                exists = True
                break
        if not exists:
            self.maxkeys[route.maxkeys] = [route]
        self._created_gens = False
    
    def _create_gens(self):
        """Create the generation hashes for route lookups"""
        # Use keys temporailly to assemble the list to avoid excessive
        # list iteration testing with "in"
        controllerlist = {}
        actionlist = {}
        
        # Assemble all the hardcoded/defaulted actions/controllers used
        for route in self.matchlist:
            if route.static:
                continue
            if route.defaults.has_key('controller'):
                controllerlist[route.defaults['controller']] = True
            if route.defaults.has_key('action'):
                actionlist[route.defaults['action']] = True
        
        # Setup the lists of all controllers/actions we'll add each route
        # to. We include the '*' in the case that a generate contains a
        # controller/action that has no hardcodes
        controllerlist = controllerlist.keys() + ['*']
        actionlist = actionlist.keys() + ['*']
        
        # Go through our list again, assemble the controllers/actions we'll
        # add each route to. If its hardcoded, we only add it to that dict key.
        # Otherwise we add it to every hardcode since it can be changed.
        gendict = {} # Our generated two-deep hash
        for route in self.matchlist:
            if route.static:
                continue
            clist = controllerlist
            alist = actionlist
            if 'controller' in route.hardcoded:
                clist = [route.defaults['controller']]
            if 'action' in route.hardcoded:
                alist = [unicode(route.defaults['action'])]
            for controller in clist:
                for action in alist:
                    actiondict = gendict.setdefault(controller, {})
                    actiondict.setdefault(action, ([], {}))[0].append(route)
        self._gendict = gendict
        self._created_gens = True

    def create_regs(self, *args, **kwargs):
        """Atomically creates regular expressions for all connected
        routes
        """
        self.create_regs_lock.acquire()
        try:
            self._create_regs(*args, **kwargs)
        finally:
            self.create_regs_lock.release()
    
    def _create_regs(self, clist=None):
        """Creates regular expressions for all connected routes"""
        if clist is None:
            if self.directory:
                clist = self.controller_scan(self.directory)
            else:
                clist = self.controller_scan()
            
        for key, val in self.maxkeys.iteritems():
            for route in val:
                route.makeregexp(clist)
        
        
        # Create our regexp to strip the prefix
        if self.prefix:
            self._regprefix = re.compile(self.prefix + '(.*)')
        self._created_regs = True
    
    def _match(self, url):
        """Internal Route matcher
        
        Matches a URL against a route, and returns a tuple of the match
        dict and the route object if a match is successfull, otherwise
        it returns empty.
        
        For internal use only.
        
        """
        if not self._created_regs and self.controller_scan:
            self.create_regs()
        elif not self._created_regs:
            raise RouteException("You must generate the regular expressions"
                                 " before matching.")
        
        if self.always_scan:
            self.create_regs()
        
        matchlog = []
        if self.prefix:
            if re.match(self._regprefix, url):
                url = re.sub(self._regprefix, r'\1', url)
                if not url:
                    url = '/'
            else:
                return (None, None, matchlog)
        for route in self.matchlist:
            if route.static:
                if self.debug:
                    matchlog.append(dict(route=route, static=True))
                continue
            match = route.match(url, self.environ, self.sub_domains, 
                self.sub_domains_ignore, self.domain_match)
            if self.debug:
                matchlog.append(dict(route=route, regexp=bool(match)))
            if match:
                return (match, route, matchlog)
        return (None, None, matchlog)
    
    def match(self, url):
        """Match a URL against against one of the routes contained.
        
        Will return None if no valid match is found.
        
        .. code-block:: python
            
            resultdict = m.match('/joe/sixpack')
        
        """
        if not url:
            raise RouteException('No URL provided, the minimum URL necessary'
                                 ' to match is "/".')
        
        result = self._match(url)
        if self.debug:
            return result[0], result[1], result[2]
        if result[0]:
            return result[0]
        return None
    
    def routematch(self, url):
        """Match a URL against against one of the routes contained.
        
        Will return None if no valid match is found, otherwise a
        result dict and a route object is returned.
        
        .. code-block:: python
        
            resultdict, route_obj = m.match('/joe/sixpack')
        
        """
        result = self._match(url)
        if self.debug:
            return result[0], result[1], result[2]
        if result[0]:
            return result[0], result[1]
        return None
    
    def generate(self, *args, **kargs):
        """Generate a route from a set of keywords
        
        Returns the url text, or None if no URL could be generated.
        
        .. code-block:: python
            
            m.generate(controller='content',action='view',id=10)
        
        """
        # Generate ourself if we haven't already
        if not self._created_gens:
            self._create_gens()
        
        if self.append_slash:
            kargs['_append_slash'] = True
                
        if not self.explicit:
            if 'controller' not in kargs:
                kargs['controller'] = 'content'
            if 'action' not in kargs:
                kargs['action'] = 'index'
        
        controller = kargs.get('controller', None)
        action = kargs.get('action', None)

        # If the URL didn't depend on the SCRIPT_NAME, we'll cache it
        # keyed by just by kargs; otherwise we need to cache it with
        # both SCRIPT_NAME and kargs:
        cache_key = unicode(args).encode('utf8') + \
            unicode(kargs).encode('utf8')
        
        if self.urlcache is not None:
            if self.environ:
                cache_key_script_name = '%s:%s' % (
                    self.environ.get('SCRIPT_NAME', ''), cache_key)
            else:
                cache_key_script_name = cache_key
        
            # Check the url cache to see if it exists, use it if it does
            for key in [cache_key, cache_key_script_name]:
                if key in self.urlcache:
                    return self.urlcache[key]
        
        actionlist = self._gendict.get(controller) or self._gendict.get('*')
        if not actionlist:
            return None
        (keylist, sortcache) = actionlist.get(action) or \
                               actionlist.get('*', (None, None))
        if not keylist:
            return None
        
        keys = frozenset(kargs.keys())
        cacheset = False
        cachekey = unicode(keys)
        cachelist = sortcache.get(cachekey)
        if args:
            keylist = args
        elif cachelist:
            keylist = cachelist
        else:
            cacheset = True
            newlist = []
            for route in keylist:
                if len(route.minkeys-keys) == 0:
                    newlist.append(route)
            keylist = newlist
            
            def keysort(a, b):
                """Sorts two sets of sets, to order them ideally for
                matching."""
                am = a.minkeys
                a = a.maxkeys
                b = b.maxkeys
                
                lendiffa = len(keys^a)
                lendiffb = len(keys^b)
                # If they both match, don't switch them
                if lendiffa == 0 and lendiffb == 0:
                    return 0
                
                # First, if a matches exactly, use it
                if lendiffa == 0:
                    return -1
                
                # Or b matches exactly, use it
                if lendiffb == 0:
                    return 1
                
                # Neither matches exactly, return the one with the most in 
                # common
                if cmp(lendiffa, lendiffb) != 0:
                    return cmp(lendiffa, lendiffb)
                
                # Neither matches exactly, but if they both have just as much 
                # in common
                if len(keys&b) == len(keys&a):
                    # Then we return the shortest of the two
                    return cmp(len(a), len(b))
                
                # Otherwise, we return the one that has the most in common
                else:
                    return cmp(len(keys&b), len(keys&a))
            
            keylist.sort(keysort)
            if cacheset:
                sortcache[cachekey] = keylist
        
        # Iterate through the keylist of sorted routes (or a single route if
        # it was passed in explicitly for hardcoded named routes)
        for route in keylist:
            fail = False
            for key in route.hardcoded:
                kval = kargs.get(key)
                if not kval:
                    continue
                if kval != route.defaults[key]:
                    fail = True
                    break
            if fail:
                continue
            path = route.generate(**kargs)
            if path:
                if self.prefix:
                    path = self.prefix + path
                if self.environ and self.environ.get('SCRIPT_NAME', '') != ''\
                    and not route.absolute:
                    path = self.environ['SCRIPT_NAME'] + path
                    key = cache_key_script_name
                else:
                    key = cache_key
                if self.urlcache is not None:
                    self.urlcache[key] = str(path)
                return str(path)
            else:
                continue
        return None
    
    def resource(self, member_name, collection_name, **kwargs):
        """Generate routes for a controller resource
        
        The member_name name should be the appropriate singular version
        of the resource given your locale and used with members of the
        collection. The collection_name name will be used to refer to
        the resource collection methods and should be a plural version
        of the member_name argument. By default, the member_name name
        will also be assumed to map to a controller you create.
        
        The concept of a web resource maps somewhat directly to 'CRUD' 
        operations. The overlying things to keep in mind is that
        mapping a resource is about handling creating, viewing, and
        editing that resource.
        
        All keyword arguments are optional.
        
        ``controller``
            If specified in the keyword args, the controller will be
            the actual controller used, but the rest of the naming
            conventions used for the route names and URL paths are
            unchanged.
        
        ``collection``
            Additional action mappings used to manipulate/view the
            entire set of resources provided by the controller.
            
            Example::
                
                map.resource('message', 'messages', collection={'rss':'GET'})
                # GET /message/rss (maps to the rss action)
                # also adds named route "rss_message"
        
        ``member``
            Additional action mappings used to access an individual
            'member' of this controllers resources.
            
            Example::
                
                map.resource('message', 'messages', member={'mark':'POST'})
                # POST /message/1/mark (maps to the mark action)
                # also adds named route "mark_message"
        
        ``new``
            Action mappings that involve dealing with a new member in
            the controller resources.
            
            Example::
                
                map.resource('message', 'messages', new={'preview':'POST'})
                # POST /message/new/preview (maps to the preview action)
                # also adds a url named "preview_new_message"
        
        ``path_prefix``
            Prepends the URL path for the Route with the path_prefix
            given. This is most useful for cases where you want to mix
            resources or relations between resources.
        
        ``name_prefix``
            Perpends the route names that are generated with the
            name_prefix given. Combined with the path_prefix option,
            it's easy to generate route names and paths that represent
            resources that are in relations.
            
            Example::
                
                map.resource('message', 'messages', controller='categories', 
                    path_prefix='/category/:category_id', 
                    name_prefix="category_")
                # GET /category/7/message/1
                # has named route "category_message"
                
        ``parent_resource`` 
            A ``dict`` containing information about the parent
            resource, for creating a nested resource. It should contain
            the ``member_name`` and ``collection_name`` of the parent
            resource. This ``dict`` will 
            be available via the associated ``Route`` object which can
            be accessed during a request via
            ``request.environ['routes.route']``
 
            If ``parent_resource`` is supplied and ``path_prefix``
            isn't, ``path_prefix`` will be generated from
            ``parent_resource`` as
            "<parent collection name>/:<parent member name>_id". 

            If ``parent_resource`` is supplied and ``name_prefix``
            isn't, ``name_prefix`` will be generated from
            ``parent_resource`` as  "<parent member name>_". 
 
            Example:: 
 
                >>> from routes.util import url_for 
                >>> m = Mapper() 
                >>> m.resource('location', 'locations', 
                ...            parent_resource=dict(member_name='region', 
                ...                                 collection_name='regions'))
                >>> # path_prefix is "regions/:region_id" 
                >>> # name prefix is "region_"  
                >>> url_for('region_locations', region_id=13) 
                '/regions/13/locations'
                >>> url_for('region_new_location', region_id=13) 
                '/regions/13/locations/new'
                >>> url_for('region_location', region_id=13, id=60) 
                '/regions/13/locations/60'
                >>> url_for('region_edit_location', region_id=13, id=60) 
                '/regions/13/locations/60/edit'

            Overriding generated ``path_prefix``::

                >>> m = Mapper()
                >>> m.resource('location', 'locations',
                ...            parent_resource=dict(member_name='region',
                ...                                 collection_name='regions'),
                ...            path_prefix='areas/:area_id')
                >>> # name prefix is "region_"
                >>> url_for('region_locations', area_id=51)
                '/areas/51/locations'

            Overriding generated ``name_prefix``::

                >>> m = Mapper()
                >>> m.resource('location', 'locations',
                ...            parent_resource=dict(member_name='region',
                ...                                 collection_name='regions'),
                ...            name_prefix='')
                >>> # path_prefix is "regions/:region_id" 
                >>> url_for('locations', region_id=51)
                '/regions/51/locations'

        """
        collection = kwargs.pop('collection', {})
        member = kwargs.pop('member', {})
        new = kwargs.pop('new', {})
        path_prefix = kwargs.pop('path_prefix', None)
        name_prefix = kwargs.pop('name_prefix', None)
        parent_resource = kwargs.pop('parent_resource', None)
        
        # Generate ``path_prefix`` if ``path_prefix`` wasn't specified and 
        # ``parent_resource`` was. Likewise for ``name_prefix``. Make sure
        # that ``path_prefix`` and ``name_prefix`` *always* take precedence if
        # they are specified--in particular, we need to be careful when they
        # are explicitly set to "".
        if parent_resource is not None: 
            if path_prefix is None: 
                path_prefix = '%s/:%s_id' % (parent_resource['collection_name'], 
                                             parent_resource['member_name']) 
            if name_prefix is None:
                name_prefix = '%s_' % parent_resource['member_name']
        else:
            if path_prefix is None: path_prefix = ''
            if name_prefix is None: name_prefix = ''
        
        # Ensure the edit and new actions are in and GET
        member['edit'] = 'GET'
        new.update({'new': 'GET'})
        
        # Make new dict's based off the old, except the old values become keys,
        # and the old keys become items in a list as the value
        def swap(dct, newdct):
            """Swap the keys and values in the dict, and uppercase the values
            from the dict during the swap."""
            for key, val in dct.iteritems():
                newdct.setdefault(val.upper(), []).append(key)
            return newdct
        collection_methods = swap(collection, {})
        member_methods = swap(member, {})
        new_methods = swap(new, {})
        
        # Insert create, update, and destroy methods
        collection_methods.setdefault('POST', []).insert(0, 'create')
        member_methods.setdefault('PUT', []).insert(0, 'update')
        member_methods.setdefault('DELETE', []).insert(0, 'delete')
        
        # If there's a path prefix option, use it with the controller
        controller = strip_slashes(collection_name)
        path_prefix = strip_slashes(path_prefix)
        path_prefix = '/' + path_prefix
        if path_prefix and path_prefix != '/':
            path = path_prefix + '/' + controller
        else:
            path = '/' + controller
        collection_path = path
        new_path = path + "/new"
        member_path = path + "/:(id)"
        
        options = { 
            'controller': kwargs.get('controller', controller),
            '_member_name': member_name,
            '_collection_name': collection_name,
            '_parent_resource': parent_resource,
        }
        
        def requirements_for(meth):
            """Returns a new dict to be used for all route creation as the
            route options"""
            opts = options.copy()
            if method != 'any': 
                opts['conditions'] = {'method':[meth.upper()]}
            return opts
        
        # Add the routes for handling collection methods
        for method, lst in collection_methods.iteritems():
            primary = (method != 'GET' and lst.pop(0)) or None
            route_options = requirements_for(method)
            for action in lst:
                route_options['action'] = action
                route_name = "%s%s_%s" % (name_prefix, action, collection_name)
                self.connect("formatted_" + route_name, "%s/%s.:(format)" % \
                             (collection_path, action), **route_options)
                self.connect(route_name, "%s/%s" % (collection_path, action),
                                                    **route_options)
            if primary:
                route_options['action'] = primary
                self.connect("%s.:(format)" % collection_path, **route_options)
                self.connect(collection_path, **route_options)
        
        # Specifically add in the built-in 'index' collection method and its 
        # formatted version
        self.connect("formatted_" + name_prefix + collection_name, 
            collection_path + ".:(format)", action='index', 
            conditions={'method':['GET']}, **options)
        self.connect(name_prefix + collection_name, collection_path, 
                     action='index', conditions={'method':['GET']}, **options)
        
        # Add the routes that deal with new resource methods
        for method, lst in new_methods.iteritems():
            route_options = requirements_for(method)
            for action in lst:
                path = (action == 'new' and new_path) or "%s/%s" % (new_path, 
                                                                    action)
                name = "new_" + member_name
                if action != 'new':
                    name = action + "_" + name
                route_options['action'] = action
                formatted_path = (action == 'new' and new_path + '.:(format)') or \
                    "%s/%s.:(format)" % (new_path, action)
                self.connect("formatted_" + name_prefix + name, formatted_path, 
                             **route_options)
                self.connect(name_prefix + name, path, **route_options)
        
        requirements_regexp = '[^\/]+'

        # Add the routes that deal with member methods of a resource
        for method, lst in member_methods.iteritems():
            route_options = requirements_for(method)
            route_options['requirements'] = {'id':requirements_regexp}
            if method not in ['POST', 'GET', 'any']:
                primary = lst.pop(0)
            else:
                primary = None
            for action in lst:
                route_options['action'] = action
                self.connect("formatted_%s%s_%s" % (name_prefix, action, 
                                                    member_name),
                    "%s/%s.:(format)" % (member_path, action), **route_options)
                self.connect("%s%s_%s" % (name_prefix, action, member_name),
                    "%s/%s" % (member_path, action), **route_options)
            if primary:
                route_options['action'] = primary
                self.connect("%s.:(format)" % member_path, **route_options)
                self.connect(member_path, **route_options)
        
        # Specifically add the member 'show' method
        route_options = requirements_for('GET')
        route_options['action'] = 'show'
        route_options['requirements'] = {'id':requirements_regexp}
        self.connect("formatted_" + name_prefix + member_name, 
                     member_path + ".:(format)", **route_options)
        self.connect(name_prefix + member_name, member_path, **route_options)
