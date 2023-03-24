FROM oprabase

COPY compsocsite ./compsocsite
RUN cp opra_dependencies/python_packages/django_mobile -r compsocsite/django_mobile/
RUN cp opra_dependencies/python_packages/prefpy -r compsocsite/prefpy/
RUN cp opra_dependencies/settings.py compsocsite/compsocsite/settings.py
RUN cp opra_dependencies/opra_crypto.py compsocsite/polls/opra_crypto.py
COPY ../requirements.txt compsocsite/requirements.txt
USER oprauser
# RUN echo "alias python='python3'" >> ~/.bashrc
# RUN echo "alias pip='pip3'" >> ~/.bashrc
# RUN echo "alias brc='source ~/.bashrc'" >> ~/.bashrc
# RUN echo "PYTHON_HOME='/usr/bin/python3.11'">> ~/.bashrc
RUN echo "PYTHON_HOME='/usr/local/bin/python'">> ~/.bashrc
RUN echo PATH='"/home/oprauser/.local/bin:$PYTHON_HOME:$HOME:$PATH"'>> ~/.bashrc
RUN pip install -r compsocsite/requirements.txt  --user

WORKDIR /compsocsite/
ENTRYPOINT /bin/bash
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]