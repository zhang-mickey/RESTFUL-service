# RESTFUL-service
Asignment 1: URL shortening service

## New identifiers
First,we encode the original URLs using hash function;
Second,check if they already exist in the database.

## database 


## GET
Returns a list of all stored short URL identifiers.

## POST

 URL to shorten 

Creates a new shortened URL and returns its id. If URL is invalid, returns 400.
## {id} GET

Redirects to the original URL corresponding to id. If not found, returns 404.

## {id} PUT
Updates the existing id mapping with a new URL.

## DETELE

## Redirect
redirect users to the original URL when they enter a shortened URL.

# Use Postman test the endpoints 
