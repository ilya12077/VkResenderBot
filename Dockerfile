FROM python:3.11-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y emacs &&\
    apt-get autoremove -y
	
# Install software 
RUN apt-get install -y git


# Clone the conf files into the docker container
RUN git clone https://github.com/ilya12077/VkResenderBot.git
	
	
RUN cp -a ./VkResenderBot/. /etc/vkresender/
RUN rm -r -f ./VkResenderBot/

RUN pip install requests waitress flask python-dotenv

ENV AM_I_IN_A_DOCKER_CONTAINER Yes
EXPOSE 8882/tcp
CMD ["python", "/etc/vkresender/vk.py"]

