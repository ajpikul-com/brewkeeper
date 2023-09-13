package main

import (
	"context"
	"os"

	"github.com/jackc/pgx/v5"
	"path/filepath"
)
func main() {
	id := os.Args[1]
	conn, err := pgx.Connect(context.Background(), "postgres://brewkeeper:brewdyhewdydew@george.local:5432/brew_records")

	if err != nil {
		panic("Oops, " + err.Error())
	}
	defer conn.Close(context.Background())

	binary := []byte("")
	name := ""
	err = conn.QueryRow(context.Background(), "select photo, filename from photos where id=$1", id).Scan(&binary, &name)
	if err != nil {
		panic(err.Error())
	}

	file, _ := os.Create(filepath.Base(name))
	defer file.Close()
	file.Write(binary)
}
