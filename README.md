# circum

![build](https://travis-ci.com/LumineerLabs/circum.svg?branch=master)

Circum is a distributed, multi sensor fusion system for detecting and tracking people. It applies techniques similar to systems developed for autonomous vehicles to detect and track moving objects (DATMO). Circum uses late fusion, meaning that detections are classified per sensor and then fused (associated and deduplicated) and tracked after. Because different sensors provide different capabilities (e.g. point vs volume detection), these properties will be combined in the final tracking output.

Circum is intended for art installations wanting to use human presence as an input into an interactive installation.

![architecture block diagram](./docs/architecture_block.png)

## Service

The circum service can be started with unique name and either a list of endpoints to connect to or it will find and connect to all circum endpoints on a network. Once connected to the endpoints, it will use pose and field of view information from each endpoint to combine tracking data into a single view which it will then transmit to clients whenever updated.

### Discovery

The circum service will advertise itself via zeroconf service discovery. It will advertise under

```console
<name>._service._circum._tcp.local.
```

## Endpoints

Endpoints perform detection and classification and transmit information about the detected objects to the core service. At the very least, the endpoint must transmit a centroid of a detected person. The core service operates on this. Any additional information is added into the fused track for clients to consume. Each endpoint is exposed as a discoverable zeroconf service. A given tracker service is configured with a unique name and field of view information.

Supported trackers include:

* Walabot

Plans for future trackers include:

* Camera
* Kinect
* FLIR Camera

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

## Demo

## References
Circum would not have been possible without the following references:

* R. Omar Chavez-Garcia. [Multiple Sensor Fusion for Detection, Classification and Tracking of MovingObjects in Driving Environments.](https://icave2.cse.buffalo.edu/resources/sensor-modeling/sensor%20fusion.pdf) Robotics \[cs.RO\]. Université de Grenoble, 2014. English. <tel-01082021>
* [Sensor Fusion and Object Tracking using an Extended Kalman Filter Algorithm — Part 1](https://medium.com/@mithi/object-tracking-and-fusing-sensor-measurements-using-the-extended-kalman-filter-algorithm-part-1-f2158ef1e4f0) & [Part 2](https://medium.com/@mithi/sensor-fusion-and-object-tracking-using-an-extended-kalman-filter-algorithm-part-2-cd20801fbeff)