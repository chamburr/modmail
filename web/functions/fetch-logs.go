package main

import (
	"context"
	"encoding/json"
	"io/ioutil"
	"net/http"
	"regexp"
	"strconv"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-lambda-go/lambdacontext"
)

type ErrResponse struct {
	Error string `json:"error"`
}

type MsgEntry struct {
	Timestamp     string   `json:"timestamp"`
	Username      string   `json:"username"`
	Discriminator string   `json:"discriminator"`
	Role          string   `json:"role"`
	Message       string   `json:"message"`
	Attachments   []string `json:"attachments"`
}

func newResponse(statusCode int, body interface{}) (*events.APIGatewayProxyResponse, error) {
	res, err := json.Marshal(body)

	if err != nil {
		resp, _ := json.Marshal(ErrResponse{Error: "Internal Server Error"})

		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Headers:    map[string]string{"Content-Type": "application/json"},
			Body:       string(resp),
		}, nil
	}

	return &events.APIGatewayProxyResponse{
		StatusCode: statusCode,
		Headers:    map[string]string{"Content-Type": "application/json"},
		Body:       string(res),
	}, nil
}

func handler(ctx context.Context, request events.APIGatewayProxyRequest) (*events.APIGatewayProxyResponse, error) {
	if _, ok := lambdacontext.FromContext(ctx); !ok {
		return newResponse(503, ErrResponse{Error: "Service Unavailable"})
	}

	if _, ok := request.QueryStringParameters["id"]; !ok {
		return newResponse(400, ErrResponse{Error: "Bad Request"})
	}

	id := strings.Split(request.QueryStringParameters["id"], "-")

	if len(id) != 3 {
		return newResponse(404, ErrResponse{Error: "Not Found"})
	}

	newId := make([]string, 0, 3)

	for _, element := range id {
		newElement, err := strconv.ParseInt(element, 16, 64)

		if err != nil {
			return newResponse(404, ErrResponse{Error: "Not Found"})
		}

		newId = append(newId, strconv.FormatInt(newElement, 10))
	}

	resp, err := http.Get("https://cdn.discordapp.com/attachments/" + newId[0] + "/" + newId[1] + "/modmail_log_" + newId[2] + ".txt")

	if err != nil || resp.StatusCode != 200 {
		return newResponse(404, ErrResponse{Error: "Not Found"})
	}

	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)

	if err != nil {
		return newResponse(500, ErrResponse{Error: "Internal Server Error"})
	}

	messages := make([]MsgEntry, 0)

	re := regexp.MustCompile(`^\[[0-9-]{10} [0-9:]{8}\] [^\n]*#[0-9]{4} \((User|Staff|Comment)\):`)

	for _, line := range strings.Split(string(body), "\n") {
		if !re.MatchString(line) {
			if i := len(messages); i > 0 {
				messages[i-1].Message += "\n" + line
			}
			continue
		}

		newLine := strings.Split(line, "#")
		partOne := newLine[0]
		partTwo := strings.Join(newLine[1:], "#")
		timestamp := partOne[1:20]
		username := partOne[22:]
		discriminator := partTwo[:4]

		role := "User"

		if strings.HasPrefix(partTwo[6:], "Staff") {
			role = "Staff"
		} else if strings.HasPrefix(partTwo[6:], "Comment") {
			role = "Comment"
		}

		message := strings.Join(strings.Split(partTwo, ": ")[1:], ": ")

		if strings.HasPrefix(message, "(Attachment: ") {
			message = " " + message
		}

		attachment := strings.Join(strings.Split(message, " (Attachment: ")[1:], " (Attachment: ")
		message = strings.Split(message, " (Attachment: ")[0]

		attachments := make([]string, 0)

		for _, element := range strings.Split(attachment, ") (Attachment: ") {
			if strings.HasSuffix(element, ")") {
				element = element[:len(element)-1]
			}

			if element != "" {
				attachments = append(attachments, element)
			}
		}

		messages = append(messages, MsgEntry{
			Timestamp:     timestamp,
			Username:      username,
			Discriminator: discriminator,
			Role:          role,
			Message:       message,
			Attachments:   attachments,
		})
	}

	return newResponse(200, messages)
}

func main() {
	lambda.Start(handler)
}
