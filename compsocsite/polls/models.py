from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils import timezone
from django.utils.six import python_2_unicode_compatible
from django.contrib.auth.models import User
import os
from django.conf import settings

# Models

class Classes(models.Model):
    title = models.CharField(max_length=100, default="")
    startDate = models.DateField('start date')
    weekly = models.IntegerField(default=0)
    teacher = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    attendance = models.IntegerField(default=-1)
    teachingAssistants = models.ManyToManyField(User, related_name='tas')
    students = models.ManyToManyField(User, related_name='students')


# question that will receive responses
@python_2_unicode_compatible
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    question_desc = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='static/img/items/', blank=True, null=True)
    imageURL = models.CharField(max_length=500, blank=True, null=True)
    pub_date = models.DateTimeField('date published')
    follow_up = models.OneToOneField('Question', on_delete=models.CASCADE, null = True, blank = True)
    question_owner = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    question_voters = models.ManyToManyField(User, related_name='poll_participated')
    status = models.IntegerField(default=1)
    display_pref = models.IntegerField(default=1)
    creator_pref = models.IntegerField(default=1)
    emailInvite = models.BooleanField(default=True)
    emailDelete = models.BooleanField(default=True)
    emailStart = models.BooleanField(default=True)
    emailStop = models.BooleanField(default=True)
    poll_algorithm = models.IntegerField(default=1)
    question_type = models.IntegerField(default=1)
    winner = models.CharField(max_length=200,default="")
    mixtures_pl1 = models.TextField(default="")
    mixtures_pl2 = models.TextField(default="")
    mixtures_pl3 = models.TextField(default="")
    m_poll = models.BooleanField(default=False)
    next = models.IntegerField(default=-1)
    first = models.IntegerField(default=-1)
    open = models.IntegerField(default=0)
    new_vote = models.BooleanField(default=False)
    twocol_enabled = models.BooleanField(default=True)
    onecol_enabled = models.BooleanField(default=True)
    slider_enabled = models.BooleanField(default=True)
    star_enabled = models.BooleanField(default=True)
    yesno_enabled = models.BooleanField(default=True)
    yesno2_enabled = models.BooleanField(default=False)
    single_enabled = models.BooleanField(default=False)
    allowties = models.BooleanField(default=True)
    initial_ui = models.IntegerField(default=1)
    ui_number = models.IntegerField(default=6)
    vote_rule = models.IntegerField(default=4095)
    first_tier = models.IntegerField(default=0)
    utility_model = models.IntegerField(default=0)

    related_class = models.ForeignKey(Classes, null=True, on_delete=models.CASCADE)
    correct_answer = models.TextField(default="")
    allow_self_sign_up = models.IntegerField(default=0)
    def __str__(self):
        return self.question_text
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    def get_voters(self):
        return ",".join([str(voter) for voter in self.question_voters.all()])

# email to be sent
@python_2_unicode_compatible
class Folder(models.Model):
    questions = models.ManyToManyField(Question)
    user      = models.ForeignKey(User, on_delete=models.CASCADE)
    title     = models.CharField(max_length=500)
    edit_date = models.DateTimeField()
    def __str__(self):
        return self.title

# email to be sent
@python_2_unicode_compatible
class Email(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    type     = models.IntegerField()
    subject  = models.CharField(max_length=100)
    message  = models.CharField(max_length=500)
    def __str__(self):
        return self.question

#Helper function for image
def get_image_path(instance, filename):
    return 'static/img/items/'

# item to rank in a question
@python_2_unicode_compatible
class Item(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    item_text = models.CharField(max_length=200)
    item_description = models.CharField(max_length=1000, blank=True, null=True)
    image = models.ImageField(upload_to='static/img/items/', blank=True, null=True)
    imageURL = models.CharField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField('item timestamp')
    recently_added = models.BooleanField(default=False)
    utility = models.FloatField(default=0.0)
    self_sign_up_user_id = models.TextField(default="")
    def __str__(self):
        return self.item_text
    class Meta:
        ordering = ['timestamp']

# all information pertaining to a response that a student made to a question
@python_2_unicode_compatible
class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    resp_str = models.CharField(max_length=1000, null=True, blank=True)
    user = models.ForeignKey(User, null = True, blank = True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField('response timestamp')
    allocation = models.ForeignKey(Item, default=None, null = True, blank = True, on_delete=models.CASCADE) # assigned by algorithm function
    anonymous_voter = models.CharField(max_length=50,blank=True,null=True)
    anonymous_id = models.IntegerField(default = 0)
    comment = models.CharField(max_length=1000, blank=True, null=True)
    active = models.IntegerField(default=1)
    behavior_data = models.TextField(default="")
    def __str__(self):
        if self.user:
            return "Response of user " + self.user.username + "\nfor question " + self.question.question_text
        else:
            return "Response of user " + self.anonymous_voter + "\nfor question " + self.question.question_text
    class Meta:
        ordering = ['timestamp']

# all information pertaining to a response that a student made to a question
@python_2_unicode_compatible
class EmailResponse(models.Model):
    identity = models.CharField(max_length=20, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    def __str__(self):
        return ""     

# a winner at a certain point in time
@python_2_unicode_compatible
class OldWinner(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    def __str__(self):
        return (str(self.response.timestamp.time()))

# a single voter in the allocation
@python_2_unicode_compatible
class AllocationVoter(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE, null=True)
    def __str__(self):
        return "User " + self.user.username + " assigned to " + self.question.question_text 

# Dictionary Helper Models - from https://djangosnippets.org/snippets/2451/
# Models include modifications to be used specifically for holding student preferences - these changes are marked with comments

# collection of a student's preferences within a single response (to a single question)
class Dictionary(models.Model):
    """A model that represents a dictionary. This model implements most of the dictionary interface,
    allowing it to be used like a python dictionary.
    """
    name = models.CharField(max_length=255)
    response = models.ForeignKey(Response, default=None, on_delete=models.CASCADE) # added to original model
    @staticmethod
    def getDict(name):
        """Get the Dictionary of the given name.
        """
        df = Dictionary.objects.select_related().get(name=name)
        return df

    def __getitem__(self, key):
        """Returns the value of the selected key.
        """
        return self.keyvaluepair_set.get(key=key).value

    def __setitem__(self, key, value):
        """Sets the value of the given key in the Dictionary.
        """
        try:
            kvp = self.keyvaluepair_set.get(key=key)
        except KeyValuePair.DoesNotExist:
            KeyValuePair.objects.create(container=self, key=key, value=value)
        else:
            kvp.value = value
            kvp.save()

    def __delitem__(self, key):
        """Removed the given key from the Dictionary.
        """
        try:
            kvp = self.keyvaluepair_set.get(key=key)
        except KeyValuePair.DoesNotExist:
            raise KeyError
        else:
            kvp.delete()

    def __len__(self):
        """Returns the length of this Dictionary.
        """
        return self.keyvaluepair_set.count()

    def iterkeys(self):
        """Returns an iterator for the keys of this Dictionary.
        """
        return iter(kvp.key for kvp in self.keyvaluepair_set.all())

    def itervalues(self):
        """Returns an iterator for the values of this Dictionary.
        """
        return iter(kvp.value for kvp in self.keyvaluepair_set.all())

    __iter__ = iterkeys

    def iteritems(self):
        """Returns an iterator over the tuples of this Dictionary.
        """
        return iter((kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all())

    def keys(self):
        """Returns all keys in this Dictionary as a list.
        """
        return [kvp.key for kvp in self.keyvaluepair_set.all()]

    def values(self):
        """Returns all values in this Dictionary as a list.
        """
        return [kvp.value for kvp in self.keyvaluepair_set.all()]

    def sorted_values(self):
        """Sorts the Dictionary by value"""
        return list(sorted(self.items(), key=lambda kv: (kv[1], str(kv[0]))))

    def items(self):
        """Get a list of tuples of key, value for the items in this Dictionary.
        This is modeled after dict.items().
        """
        return [(kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all()]

    def get(self, key, default=None):
        """Gets the given key from the Dictionary. If the key does not exist, it
        returns default.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def has_key(self, key):
        """Returns true if the Dictionary has the given key, false if not.
        """
        return self.contains(key)

    def contains(self, key):
        """Returns true if the Dictionary has the given key, false if not.
        """
        try:
            self.keyvaluepair_set.get(key=key)
            return True
        except KeyValuePair.DoesNotExist:
            return False

    def clear(self):
        """Deletes all keys in the Dictionary.
        """
        self.keyvaluepair_set.all().delete()

    def __unicode__(self):
        """Returns a unicode representation of the Dictionary.
        """
        return unicode(self.asPyDict())

    def asPyDict(self):
        """Get a python dictionary that represents this Dictionary object.
        This object is read-only.
        """
        fieldDict = dict()
        for kvp in self.keyvaluepair_set.all():
            fieldDict[kvp.key] = kvp.value
        return fieldDict

# key-value pair of an item and the ranking a student gave it in their response
class KeyValuePair(models.Model):
    """A Key-Value pair with a pointer to the Dictionary that owns it.
    """
    container = models.ForeignKey(Dictionary, db_index=True, on_delete=models.CASCADE)
    key = models.ForeignKey(Item, default=None, on_delete=models.CASCADE, db_index=True) # changed from original model
    value = models.IntegerField(default=0, db_index=True) # changed from original model
    
class FinalResult(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    result_string = models.TextField(default="")
    mov_string = models.TextField(default="")
    node_string = models.TextField(default="")
    edge_string = models.TextField(default="")
    shade_string = models.TextField(default="")
    cand_num = models.IntegerField(default = 1)
    timestamp = models.DateTimeField('result timestamp')

class VoteResult(models.Model):
    question = models.ForeignKey(Question, null=True, on_delete=models.CASCADE)
    result_string = models.TextField(default="")
    mov_string = models.TextField(default="")
    cand_num = models.IntegerField(default = 1)
    timestamp = models.DateTimeField('result timestamp')
    class Meta:
        ordering = ['-timestamp']
        
class MoV(models.Model):
    result = models.ForeignKey(VoteResult, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    class Meta:
        ordering = ['order']
    
class ScoreMap(models.Model):
    result = models.ForeignKey(VoteResult, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    def asPyDict(self):
        """Get a python dictionary that represents this Dictionary object.
        This object is read-only.
        """
        fieldDict = dict()
        for kvp in self.candscorepair_set.all():
            fieldDict[kvp.cand] = kvp.score
        return fieldDict
    class Meta:
        ordering = ['order']

class CandScorePair(models.Model):
    container = models.ForeignKey(ScoreMap, on_delete=models.CASCADE)
    cand = models.IntegerField(default = 0)
    score = models.FloatField(default = 0.0)
    
class UserVoteRecord(models.Model):
    timestamp = models.DateTimeField('record timestamp')
    user =models.CharField(max_length=100,default="(Anonymous)")
    question = models.ForeignKey(Question,default=None, on_delete=models.CASCADE)
    record = models.CharField(max_length=10000,default="")
    col = models.TextField(default="")
    one_col = models.TextField(default="")
    slider = models.TextField(default="")
    star = models.TextField(default="")
    swit = models.TextField(default="")
    initial_order = models.TextField(default="")
    initial_type = models.IntegerField(default=0)
    final_order = models.TextField(default="")
    device = models.CharField(default="",max_length=20)
    comment_time = models.CharField(max_length=100,default="")
    submit_time = models.CharField(max_length=100,default="")
    ui = models.CharField(max_length=100,default="")
    class Meta:
        ordering = ['timestamp']

class Message(models.Model):
    text = models.CharField(max_length=10000, default="")
    timestamp = models.DateTimeField('message timestamp')
    email = models.CharField(max_length=100, default="")
    name = models.CharField(max_length=200, default="")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)

class Experiment(models.Model):
    title = models.CharField(max_length=10000)
    timestamp = models.DateTimeField('date/time created')
    polls = models.TextField(default="[]")
    status = models.IntegerField(default=0)
    participants = models.ManyToManyField(User)

class RandomUtilityPool(models.Model):
    data = models.TextField(default="[]")

class SignUpRequest(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.TextField()
    status = models.IntegerField(default=1)
    timestamp = models.DateTimeField('request timestamp')

