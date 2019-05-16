# circum

Proximity interaction service combining inputs from multiple tracking device endpoints.

## Core Service

The circum service can be started with unique name and either a list of endpoints to connect to or it will find and connect to all circum endpoints on a network. Once connected to the endpoints, it will use pose and field of view information from each endpoint to combine tracking data into a single view which it will then transmit to clients whenever updated.

### Discovery

The circum service will advertise itself via zeroconf service discovery. It will advertise under

```console
<name>._service._circum._tcp.local.
```

## Endpoints

Each endpoint is exposed as a discoverable zeroconf service. A given tracker service is configured with a unique name and field of view information.

Supported trackers include:

* Walabot

Plans for future trackers include:

* FLIR Camera
* Kinect

### Discovery

The endpoints will advertise under

```console
<name>._endpoint._sub._circum._tcp.local.
```

The type of endpoint will be noted in the service properties

|    Type     | Type Tag |
|-------------|----------|
| Walabot     |  walabot |
| FLIR Camera |  flir    |
| Kinect      |  kinect  |
