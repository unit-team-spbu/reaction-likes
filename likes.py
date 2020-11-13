from nameko.web.handlers import http
from nameko.rpc import rpc, RpcProxy
from nameko.events import EventDispatcher
from nameko_mongodb import MongoDatabase
from werkzeug.wrappers import Request, Response
import json


class Likes:
    # Vars

    name = "likes"

    db = MongoDatabase()
    '''
        name of collection: 'likes';
        columns:
                '_id' - id of the user
                'likes_list' - the list:
                    [event_1_id, ..., event_m_id]
    '''

    logger_rpc = RpcProxy('logger')

    dispatch = EventDispatcher()
    '''
        calling for service 'uis' if new like was made
    '''

    # Logic

    def _new_like(self, like_data) -> bool:
        '''
         like_data is [user_id, event_id]
         Save info in database
         Returns True if new info is added, False otherwise
        '''
        user_id, event_id = like_data
        collection = self.db["likes"]

        current_likes_list = collection.find_one(
            {"_id": user_id},
            {"likes_list": 1}
        )  # check whether this user is presented in db

        if current_likes_list:
            # this user is presented
            current_likes_list = current_likes_list["likes_list"]
            if event_id not in current_likes_list:
                # add event_id in the list
                current_likes_list.append(event_id)
                collection.update_one(
                    {'_id': user_id},
                    {'$set': {"likes_list": current_likes_list}}
                )
                return True
            # change nothing
            return False
        else:
            # this is the first like
            collection.insert_one(
                {"_id": user_id, "likes_list": [event_id]}
            )
            return True

    def _cancel_like(self, like_data) -> bool:
        '''
         like_data is [user_id, event_id]
         Delete info from database
         Returns True if some info is deleted, False otherwise
        '''
        user_id, event_id = like_data
        collection = self.db["likes"]
        try:
            current_likes_list = collection.find_one(
                {"_id": user_id},
                {"likes_list": 1}
            )["likes_list"]
        except Exception:
            print(Exception)
            return False
        if event_id in current_likes_list:
            if len(current_likes_list) > 1:
                '''
                just delete one item in list
                '''
                current_likes_list.remove(event_id)
                collection.update_one(
                    {'_id': user_id},
                    {'$set': {"likes_list": current_likes_list}}
                )
            else:
                '''
                it was the last like
                delete all record in db 
                '''
                collection.delete_one(
                    {"_id": user_id}
                )
            return True
        return False

    def _get_likes(self, user_id):
        collection = self.db["likes"]
        likes = collection.find_one(
            {"_id": user_id},
            {"likes_list": 1}
        )
        if likes:
            return likes["likes_list"]
        else:
            return None

    # API

    @rpc
    def new_like(self, like_data):
        '''
            Args: like_data - [user_id, event_id] 
            dispatch to the uis - [user_id, event_id] 
        '''
        self.logger_rpc.log(self.name, self.new_like.__name__,
                            like_data, "Info", "Saving like")
        is_new_info = self._new_like(like_data)
        if is_new_info:
            self.dispatch("like", like_data)

    @rpc
    def cancel_like(self, like_data):
        '''
            Args: like_data - [user_id, event_id] 
            dispatch to the uis - [user_id, event_id] 
        '''
        self.logger_rpc.log(self.name, self.cancel_like.__name__,
                            like_data, "Info", "Cancelling like")
        is_deleted_info = self._cancel_like(like_data)
        if is_deleted_info:
            self.dispatch("like_cancel", like_data)
        else:
            print('ERROR: we try to cancel a like which we does not have gotten')

    @rpc
    def get_likes_by_id(self, user_id):
        '''
            Args: user_id
            Returns: [event_1_id, ..., event_n_id]
        '''
        return self._get_likes(user_id)

    @rpc
    def is_event_liked(self, user_id, event_id):
        '''
            Args: user_id, event_id
            Returns: bool
        '''
        likes = self._get_likes(user_id)
        if event_id in likes:
            return True
        return False

    @http("POST", "/new_like")
    def new_like_http(self, request: Request):
        '''
            POST http://localhost:8000/new_like HTTP/1.1
            Content-Type: application/json

            [user_id, event_id]
        '''
        content = request.get_data(as_text=True)
        like_data = json.loads(content)
        is_new_info = self._new_like(like_data)
        if is_new_info:
            self.dispatch("like", like_data)
        return Response(status=201)

    @http("POST", "/cancel_like")
    def cancel_like_http(self, request: Request):
        '''
            POST http://localhost:8000/cancel_like HTTP/1.1
            Content-Type: application/json

            [user_id, event_id]
        '''
        content = request.get_data(as_text=True)
        like_data = json.loads(content)
        is_deleted_info = self._cancel_like(like_data)
        if is_deleted_info:
            self.dispatch("like_cancel", like_data)
            return Response(status=201)
        '''
        else it turns out we try to cancel a like which we does not have gotten
        '''
        return Response(status=404)

    @http("GET", "/get_likes/<id>")
    def get_likes_by_id_http(self, request: Request, id):
        '''
            POST http://localhost:8000/get_likes/<id> HTTP/1.1
            Content-Type: application/json
        '''
        likes = self._get_likes(id)
        return json.dumps(likes, ensure_ascii=False)

    @http("GET", "/is_liked/<user_id>/<event_id>")
    def is_event_liked_http(self, request: Request, user_id, event_id):
        '''
            GET http://localhost:8000/is_liked/<user_id>/<event_id> HTTP/1.1
            Content-Type: application/json
        '''
        likes = self._get_likes(user_id)
        if event_id in likes:
            return json.dumps(True, ensure_ascii=False)
        return json.dumps(False, ensure_ascii=False)
