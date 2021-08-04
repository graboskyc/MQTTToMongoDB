# How To

1. Download the 3 files in this directory: `build.sh`, `Dockerfile`, and `edgeFarBiDi.py` onto the machine you want to run the container
2. Make sure docker is installed on that machine
3. Make sure it has internet access to pull the base layer and use `apt` and `pip` during the build
4. Edit the `-e` environmental variables in the `build.sh` to change the connection string and zones. Note that `WATCHZONES` is a comma delimited string. As always if the password has special characters, it must be URL encoded/escaped
5. Run `./build.sh` or `sudo ./build.sh` (if user does not have docker permissions)
6. The image will build and automatically start
7. Check the docker logs of the running container to make sure it says that it is READY and that there were no authentication errors or anything else. The first time running, it will build some metadata collections.
   ```
   Ready...

   Ready Far

   Ready Edge
   ```
8. Anything inserted into the `messages.messages` collection will be sync'd according to the partition rules defined as `ZONENAME` and `WATCHZONES`